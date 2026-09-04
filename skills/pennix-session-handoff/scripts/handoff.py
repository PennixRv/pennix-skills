#!/usr/bin/env python3
"""Create and validate a bounded, explicit-user-request-only session handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import ContractError, SECRET_RE, _text, _text_list, digest, load_json_file  # noqa: E402


SCHEMA_VERSION = 4
KIND = "pennix-session-handoff"
PARSER_VERSION = "codex-jsonl-local-v1"
HANDOFFS = ".trellis/session-handoffs"
HANDOFF_NAME = "session-handoff.json"
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
HANDOFF_ID = re.compile(r"^\d{8}T\d{12}Z$")
MAX_REQUEST_BYTES = 96 * 1024
MAX_PAYLOAD_BYTES = 512 * 1024
MAX_ROLLOUT_BYTES = 256 * 1024 * 1024
MAX_RECORD_BYTES = 8 * 1024 * 1024
MAX_CANDIDATES = 48
MAX_TEXT_BYTES = 1200
MAX_UNKNOWN_SPANS = 32
MAX_TRACKED_TOOL_IDS = 2048
AUTHORIZATION = {
    "source": "current_user_explicit_request",
    "attestation": "coordinator_asserted_not_runtime_verified",
}


def _root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    trellis = root / ".trellis"
    if not root.is_dir() or trellis.is_symlink() or not trellis.is_dir():
        raise ContractError("project root must contain a regular .trellis directory")
    return root


def _sha256_file(path: Path, maximum: Optional[int] = None) -> tuple[str, int]:
    hasher = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(256 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if maximum is not None and total > maximum:
                raise ContractError("file exceeds allowed size: %s" % path)
            hasher.update(chunk)
    return "sha256:" + hasher.hexdigest(), total


def _sha256_prefix(path: Path, length: int) -> str:
    hasher = hashlib.sha256()
    remaining = length
    with path.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(256 * 1024, remaining))
            if not chunk:
                raise ContractError("rollout prefix ended before capture boundary")
            hasher.update(chunk)
            remaining -= len(chunk)
    return "sha256:" + hasher.hexdigest()


def _project_file(root: Path, relative: str, label: str) -> Path:
    candidate = root / relative
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ContractError("%s must be project-relative" % label)
    cursor = root
    for part in relative_path.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ContractError("%s contains a symbolic path: %s" % (label, relative))
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ContractError("%s resolves outside the project: %s" % (label, relative)) from exc
    return resolved


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ContractError("%s must be a regular file: %s" % (label, path))
    return path


def _task_snapshot(root: Path) -> Optional[Dict[str, str]]:
    script = _regular_file(root / ".trellis/scripts/task.py", "task.py")
    result = subprocess.run(
        [sys.executable, str(script), "current", "--json"], cwd=root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False,
    )
    if result.returncode not in (0, 1) or result.stderr:
        raise ContractError("task.py current failed")
    try:
        current = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("task.py current returned invalid JSON") from exc
    selected = current.get("current_task") if isinstance(current, dict) else None
    if selected is None:
        return None
    if not isinstance(selected, dict):
        raise ContractError("task.py current returned an invalid task")
    raw_path = _text(selected.get("dir"), "task.dir", 1024)
    task_path = Path(raw_path)
    if task_path.is_absolute() or ".." in task_path.parts or not raw_path.startswith(".trellis/tasks/"):
        raise ContractError("active task path is unsafe")
    task_dir = _project_file(root, raw_path, "active task path")
    if not task_dir.is_dir():
        raise ContractError("active task directory is unavailable")
    entries: list[tuple[str, str, int]] = []
    for path in sorted(task_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        file_digest, file_bytes = _sha256_file(path)
        entries.append((path.relative_to(root).as_posix(), file_digest, file_bytes))
    return {
        "id": _text(selected.get("id"), "task.id", 256),
        "path": raw_path,
        "status": _text(selected.get("status"), "task.status", 64),
        "material_digest": digest(entries),
    }


def _git_snapshot(root: Path) -> Dict[str, Any]:
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=20, check=False,
        )
        if result.returncode:
            raise ContractError("git snapshot failed")
        return result.stdout.decode("utf-8", errors="strict").strip()

    branch = run("branch", "--show-current") or None
    head = run("rev-parse", "HEAD") or None
    dirty_lines = [
        line for line in run("status", "--porcelain=v1").splitlines()
        if HANDOFFS + "/" not in line and ".trellis/session-handoff" not in line
    ]
    history = [line for line in run("log", "-n", "12", "--format=%H").splitlines() if line]
    return {
        "branch": branch,
        "head": head,
        "worktree_state": "dirty" if dirty_lines else "clean",
        "dirty_paths_digest": digest(dirty_lines),
        "recent_commits": history,
    }


def _evidence_snapshot(root: Path, paths: Iterable[str]) -> list[Dict[str, Any]]:
    evidence: list[Dict[str, Any]] = []
    for relative in paths:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts or str(candidate).startswith(".trellis/.runtime/"):
            raise ContractError("evidence paths must be project-relative non-runtime paths")
        target = _regular_file(_project_file(root, relative, "evidence path"), "evidence path")
        file_digest, file_bytes = _sha256_file(target)
        evidence.append({"path": relative, "bytes": file_bytes, "sha256": file_digest})
    return evidence


def _read_rollout_path(value: Any) -> Dict[str, Optional[str]]:
    if not isinstance(value, dict) or set(value) - {"path", "session_id"} or "path" not in value:
        raise ContractError("rollout must contain path and optional session_id")
    raw_path = _text(value.get("path"), "rollout.path", 4096)
    path = Path(raw_path).expanduser()
    if not path.is_absolute() or path.is_symlink():
        raise ContractError("rollout.path must be absolute")
    session_id = value.get("session_id")
    if session_id is not None:
        session_id = _text(session_id, "rollout.session_id", 256)
    return {"path": str(path.resolve()), "session_id": session_id}


def _short_text(value: Any, maximum: int = MAX_TEXT_BYTES) -> Optional[str]:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    if SECRET_RE.search(compact):
        return "[redacted: possible credential]"
    encoded = compact.encode("utf-8")
    if len(encoded) > maximum:
        compact = encoded[:maximum].decode("utf-8", errors="ignore").rstrip() + " [truncated]"
    return compact


def _content_text(payload: Dict[str, Any]) -> Optional[str]:
    content = payload.get("content")
    if not isinstance(content, list):
        return None
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") not in {"input_text", "output_text", "text"}:
            continue
        text = _short_text(item.get("text"))
        if text:
            parts.append(text)
    return _short_text("\n".join(parts)) if parts else None


def _event_message(record_type: str, payload: Any) -> tuple[Optional[str], Optional[str]]:
    if not isinstance(payload, dict):
        return None, None
    if record_type == "event_msg":
        event_type = payload.get("type")
        if event_type == "user_message":
            return "user", _short_text(payload.get("message"))
        if event_type == "agent_message":
            return "assistant", _short_text(payload.get("message"))
        return None, None
    if record_type != "response_item" or payload.get("type") != "message":
        return None, None
    role = payload.get("role")
    if role not in {"user", "assistant"}:
        return None, None
    return role, _content_text(payload)


def _topic_key(text: str) -> Optional[str]:
    paths = re.findall(r"(?:^|\s)(?:\.?/?[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+", text)
    identifiers = re.findall(r"`([^`]{2,160})`", text)
    identifiers += re.findall(r"\b(?:issue|task)\s*#?\d+\b", text, re.IGNORECASE)
    identifiers += re.findall(r"\b[a-z][a-z0-9]+(?:-[a-z0-9]+){1,}\b", text, re.IGNORECASE)
    values = [value.strip().lower() for value in paths + identifiers if value.strip()]
    return "|".join(sorted(set(values))[:4]) or None


def _timeline_state(text: str) -> str:
    lowered = text.lower()
    if re.search(r"重新(?:认可|确认|启用)|reaccept", lowered):
        return "reaccepted"
    if re.search(r"拒绝|reject", lowered):
        return "rejected"
    if re.search(r"移除|删除|关闭|撤销|取消|不再需要|revok", lowered):
        return "revoked"
    if re.search(r"不再|不要|不需要|不是这样|错误|改为|改成|correct", lowered):
        return "corrected"
    if re.search(r"认可|批准|授权|确认|同意|开始实施|继续推进|accept|approve", lowered):
        return "accepted"
    return "proposed"


def _rollout_descriptor(raw: Dict[str, Optional[str]]) -> Dict[str, Any]:
    path = _regular_file(Path(str(raw["path"])), "rollout source")
    session_id = raw["session_id"]
    with path.open("rb") as handle:
        start = os.fstat(handle.fileno())
        if start.st_size > MAX_ROLLOUT_BYTES:
            raise ContractError("rollout exceeds %d bytes; create a new bounded session before handoff" % MAX_ROLLOUT_BYTES)
        capture_size = start.st_size
        hasher = hashlib.sha256()
        offset = line_number = record_count = event_index = 0
        candidates: list[Dict[str, Any]] = []
        timeline: list[Dict[str, Any]] = []
        latest_by_topic: Dict[str, int] = {}
        repeated: Dict[str, int] = {}
        tool_calls: Dict[str, int] = {}
        tool_results: Dict[str, int] = {}
        excluded: Dict[str, int] = {}
        unknown: Dict[str, int] = {}
        unknown_spans: list[Dict[str, Any]] = []
        omissions: list[Dict[str, Any]] = []

        def keep(items: list[Dict[str, Any]], item: Dict[str, Any]) -> None:
            if len(items) >= MAX_CANDIDATES:
                items.pop(MAX_CANDIDATES // 2)
            items.append(item)

        def count(items: Dict[str, int], key: str) -> None:
            if key in items or len(items) < MAX_UNKNOWN_SPANS:
                items[key] = items.get(key, 0) + 1
            else:
                items["other"] = items.get("other", 0) + 1
        while offset < capture_size:
            remaining = capture_size - offset
            raw_line = handle.readline(min(MAX_RECORD_BYTES + 1, remaining + 1))
            if not raw_line:
                break
            if len(raw_line) > MAX_RECORD_BYTES:
                raise ContractError("rollout record exceeds %d bytes at byte %d" % (MAX_RECORD_BYTES, offset))
            if not raw_line.endswith(b"\n") and offset + len(raw_line) < capture_size:
                raise ContractError("rollout contains an incomplete record before capture boundary")
            if not raw_line.endswith(b"\n"):
                omissions.append({"kind": "trailing_partial_record", "byte_start": offset, "bytes": len(raw_line)})
                break
            line_number += 1
            byte_start = offset
            offset += len(raw_line)
            if not raw_line.strip():
                hasher.update(raw_line)
                continue
            try:
                record = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ContractError("rollout JSONL record is invalid at line %d" % line_number) from exc
            if not isinstance(record, dict):
                raise ContractError("rollout record is not an object at line %d" % line_number)
            hasher.update(raw_line)
            record_count += 1
            record_type = str(record.get("type", "unknown"))
            payload = record.get("payload")
            source = {"line": line_number, "byte_start": byte_start, "byte_end": offset, "record_type": record_type, "record_sha256": "sha256:" + hashlib.sha256(raw_line).hexdigest()}
            if isinstance(record.get("timestamp"), str):
                source["timestamp"] = _short_text(record["timestamp"], 128)
            role, message_text = _event_message(record_type, payload)
            if role and message_text:
                event_index += 1
                keep(candidates, {"kind": role, "event_index": event_index, "text": message_text, "source": source})
                if role == "user":
                    topic = _topic_key(message_text)
                    if topic:
                        repeat_key = topic + "\0" + hashlib.sha256(message_text.encode("utf-8")).hexdigest()
                        repeated[repeat_key] = repeated.get(repeat_key, 0) + 1
                        item: Dict[str, Any] = {"topic_key": topic, "state": "repeated" if repeated[repeat_key] > 1 else _timeline_state(message_text), "event_index": event_index, "summary": message_text, "source": source, "repeat_count": repeated[repeat_key]}
                        if topic in latest_by_topic:
                            item["supersedes_event_index"] = latest_by_topic[topic]
                        latest_by_topic[topic] = event_index
                        keep(timeline, item)
                continue
            if record_type != "response_item" or not isinstance(payload, dict):
                count(unknown, record_type)
                if len(unknown_spans) < MAX_UNKNOWN_SPANS:
                    unknown_spans.append({"record_type": record_type, "line": line_number, "byte_start": byte_start, "byte_end": offset, "record_sha256": source["record_sha256"]})
                continue
            item_type = str(payload.get("type", "unknown"))
            if item_type == "reasoning":
                excluded["reasoning"] = excluded.get("reasoning", 0) + 1
                continue
            if item_type == "message":
                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    excluded["message:%s" % role] = excluded.get("message:%s" % role, 0) + 1
                    continue
                continue
            if item_type in {"function_call", "custom_tool_call", "tool_call"}:
                call_id = _short_text(payload.get("call_id") or payload.get("id"), 256)
                if call_id and len(tool_calls) < MAX_TRACKED_TOOL_IDS:
                    tool_calls[call_id] = event_index + 1
                event_index += 1
                item = {"kind": "tool_call", "event_index": event_index, "tool": _short_text(payload.get("name"), 256), "source": source}
                if call_id:
                    item["call_id"] = call_id
                keep(candidates, item)
                continue
            if item_type in {"function_call_output", "custom_tool_call_output", "tool_result"}:
                call_id = _short_text(payload.get("call_id") or payload.get("id"), 256)
                if call_id and len(tool_results) < MAX_TRACKED_TOOL_IDS:
                    tool_results[call_id] = event_index + 1
                event_index += 1
                result_text = _short_text(payload.get("output") or payload.get("result") or payload.get("error"))
                item = {"kind": "tool_result", "event_index": event_index, "source": source}
                if call_id:
                    item["call_id"] = call_id
                if result_text:
                    item["text"] = result_text
                keep(candidates, item)
                continue
            count(unknown, "response_item:%s" % item_type)
            if len(unknown_spans) < MAX_UNKNOWN_SPANS:
                unknown_spans.append({"record_type": "response_item:%s" % item_type, "line": line_number, "byte_start": byte_start, "byte_end": offset, "record_sha256": source["record_sha256"]})
        capture_end = offset
        end = os.fstat(handle.fileno())
    post = path.stat()
    if (post.st_dev, post.st_ino) != (start.st_dev, start.st_ino) or end.st_size < capture_end:
        raise ContractError("rollout source changed while being captured")
    if _sha256_prefix(path, capture_end) != "sha256:" + hasher.hexdigest():
        raise ContractError("rollout source changed while being captured")
    coverage = {
        "source_bytes_at_capture": capture_size, "capture_end": capture_end, "record_count": record_count,
        "event_count": event_index, "excluded": excluded, "unknown": unknown, "omissions": omissions,
        "unknown_spans": unknown_spans,
        "incomplete_tool_calls": sorted(set(tool_calls) ^ set(tool_results))[:32],
    }
    return {
        "path": str(path), "session_id": session_id, "device": start.st_dev, "inode": start.st_ino,
        "capture_end": capture_end, "record_count": record_count, "prefix_sha256": "sha256:" + hasher.hexdigest(),
        "parser_version": PARSER_VERSION, "coverage": coverage, "conversation_candidates": candidates[-MAX_CANDIDATES:],
        "timeline": timeline[-MAX_CANDIDATES:],
    }


def _verify_rollout(descriptor: Dict[str, Any]) -> str:
    try:
        path = _regular_file(Path(_text(descriptor.get("path"), "rollout.path", 4096)), "rollout source")
        capture_end = descriptor.get("capture_end")
        if not isinstance(capture_end, int) or capture_end < 0 or capture_end > MAX_ROLLOUT_BYTES:
            raise ContractError("rollout.capture_end is invalid")
        expected = _digest_text(descriptor.get("prefix_sha256"), "rollout.prefix_sha256")
        current = path.stat()
        if current.st_size < capture_end or (current.st_dev, current.st_ino) != (descriptor.get("device"), descriptor.get("inode")):
            return "changed"
        hasher = hashlib.sha256()
        remaining = capture_end
        with path.open("rb") as handle:
            while remaining:
                chunk = handle.read(min(256 * 1024, remaining))
                if not chunk:
                    return "changed"
                hasher.update(chunk)
                remaining -= len(chunk)
        return "ready" if "sha256:" + hasher.hexdigest() == expected else "changed"
    except (ContractError, OSError):
        return "recovery_required"


def _source(root: Path, task: Optional[Dict[str, str]], evidence: list[Dict[str, Any]], rollout: Dict[str, Any]) -> Dict[str, Any]:
    source = {
        "task": task, "git": _git_snapshot(root), "evidence": evidence,
        "rollout_identity": {key: rollout[key] for key in ("path", "session_id", "device", "inode", "capture_end", "record_count", "prefix_sha256", "parser_version")},
    }
    source["digest"] = digest(source)
    return source


def _payload_digest(payload: Dict[str, Any]) -> str:
    return digest({key: value for key, value in payload.items() if key != "integrity"})


def _digest_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_DIGEST.fullmatch(value):
        raise ContractError("%s is invalid" % label)
    return value


def _request(root: Path, path: Path) -> Dict[str, Any]:
    value = load_json_file(path, MAX_REQUEST_BYTES)
    required = {"session_label", "facts", "evidence_paths", "next_action", "blockers", "risks", "validation", "rollout"}
    if set(value) != required:
        raise ContractError("handoff request fields are invalid")
    evidence_paths = _text_list(value["evidence_paths"], "evidence_paths", 32)
    validation = value["validation"]
    if not isinstance(validation, list) or len(validation) > 16:
        raise ContractError("validation must be a list of at most 16 entries")
    normalized_validation = []
    for index, item in enumerate(validation):
        if not isinstance(item, dict) or set(item) != {"command", "result"}:
            raise ContractError("validation[%d] fields are invalid" % index)
        normalized_validation.append({"command": _text(item["command"], "validation[%d].command" % index, 512), "result": _text(item["result"], "validation[%d].result" % index, 512)})
    normalized = {
        "session_label": _text(value["session_label"], "session_label", 128), "facts": _text_list(value["facts"], "facts", 24),
        "evidence_paths": evidence_paths, "next_action": _text(value["next_action"], "next_action", 512),
        "blockers": _text_list(value["blockers"], "blockers", 16), "risks": _text_list(value["risks"], "risks", 16),
        "validation": normalized_validation, "rollout": _read_rollout_path(value["rollout"]),
    }
    _evidence_snapshot(root, evidence_paths)
    if SECRET_RE.search(json.dumps(normalized, ensure_ascii=False)):
        raise ContractError("handoff request contains a possible credential or secret")
    return normalized


def _handoff_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _destination(root: Path, handoff_path: Optional[str] = None, create_id: Optional[str] = None) -> tuple[str, Path]:
    if handoff_path is not None:
        path = _project_file(root, handoff_path, "handoff path")
        relative = path.relative_to(root).as_posix()
        match = re.fullmatch(r"\.trellis/session-handoffs/(\d{8}T\d{12}Z)/session-handoff\.json", relative)
        if not match:
            raise ContractError("handoff path must name one timestamped handoff package")
        return match.group(1), path
    if create_id is None or not HANDOFF_ID.fullmatch(create_id):
        raise ContractError("handoff id is invalid")
    base = root / HANDOFFS
    if base.is_symlink():
        raise ContractError("session-handoffs directory is unsafe")
    return create_id, base / create_id / HANDOFF_NAME


def build(root: Path, request: Dict[str, Any], handoff_id: str) -> Dict[str, Any]:
    rollout = _rollout_descriptor(request["rollout"])
    evidence = _evidence_snapshot(root, request["evidence_paths"])
    task = _task_snapshot(root)
    source = _source(root, task, evidence, rollout)
    payload: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "kind": KIND, "handoff_id": handoff_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "project": {"name": root.name, "identity_digest": digest({"name": root.name, "marker": ".trellis"})},
        "work_context": {"task": task},
        "source": {"session_label": request["session_label"], "git": source["git"], "evidence": evidence, "rollout": rollout},
        "verified": {"facts": request["facts"], "validation": request["validation"]},
        "conversation": {"candidates": rollout["conversation_candidates"], "timeline": rollout["timeline"], "coverage": rollout["coverage"]},
        "pending": {"next_action": request["next_action"], "blockers": request["blockers"], "risks": request["risks"]},
        "memory_projection": {"local": [], "archive_refs": [], "openviking": []}, "authorization": dict(AUTHORIZATION),
    }
    payload["integrity"] = {"payload_digest": _payload_digest(payload), "source_digest": source["digest"]}
    return payload


def _validate_payload_shape(root: Path, payload: Dict[str, Any], handoff_id: str) -> None:
    expected = {"schema_version", "kind", "handoff_id", "created_at", "project", "work_context", "source", "verified", "conversation", "pending", "memory_projection", "authorization", "integrity"}
    if set(payload) != expected or payload["schema_version"] != SCHEMA_VERSION or payload["kind"] != KIND:
        raise ContractError("handoff schema is unsupported")
    if payload["handoff_id"] != handoff_id or not HANDOFF_ID.fullmatch(handoff_id):
        raise ContractError("handoff id does not match package path")
    _text(payload["created_at"], "created_at", 128)
    if payload["project"] != {"name": root.name, "identity_digest": digest({"name": root.name, "marker": ".trellis"})}:
        raise ContractError("handoff project identity is invalid")
    context = payload["work_context"]
    if not isinstance(context, dict) or set(context) != {"task"}:
        raise ContractError("handoff work context is invalid")
    task = context["task"]
    if task is not None and (not isinstance(task, dict) or set(task) != {"id", "path", "status", "material_digest"}):
        raise ContractError("handoff task is invalid")
    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"session_label", "git", "evidence", "rollout"}:
        raise ContractError("handoff source is invalid")
    _text(source["session_label"], "source.session_label", 128)
    if not isinstance(source["evidence"], list) or len(source["evidence"]) > 32:
        raise ContractError("handoff evidence is invalid")
    for item in source["evidence"]:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise ContractError("handoff evidence item is invalid")
        _project_file(root, _text(item["path"], "evidence.path", 1024), "evidence path")
        if not isinstance(item["bytes"], int) or item["bytes"] < 0:
            raise ContractError("evidence bytes is invalid")
        _digest_text(item["sha256"], "evidence.sha256")
    rollout = source["rollout"]
    rollout_expected = {"path", "session_id", "device", "inode", "capture_end", "record_count", "prefix_sha256", "parser_version", "coverage", "conversation_candidates", "timeline"}
    if not isinstance(rollout, dict) or set(rollout) != rollout_expected:
        raise ContractError("handoff rollout descriptor is invalid")
    _text(rollout["path"], "rollout.path", 4096)
    if rollout["session_id"] is not None:
        _text(rollout["session_id"], "rollout.session_id", 256)
    for field in ("device", "inode", "capture_end", "record_count"):
        if not isinstance(rollout[field], int) or rollout[field] < 0:
            raise ContractError("rollout.%s is invalid" % field)
    _digest_text(rollout["prefix_sha256"], "rollout.prefix_sha256")
    if rollout["parser_version"] != PARSER_VERSION:
        raise ContractError("rollout parser version is unsupported")
    if not isinstance(rollout["coverage"], dict) or not isinstance(rollout["conversation_candidates"], list) or not isinstance(rollout["timeline"], list):
        raise ContractError("rollout summary is invalid")
    verified = payload["verified"]
    if not isinstance(verified, dict) or set(verified) != {"facts", "validation"}:
        raise ContractError("handoff verified context is invalid")
    _text_list(verified["facts"], "verified.facts", 24)
    if not isinstance(verified["validation"], list) or len(verified["validation"]) > 16:
        raise ContractError("handoff validation is invalid")
    pending = payload["pending"]
    if not isinstance(pending, dict) or set(pending) != {"next_action", "blockers", "risks"}:
        raise ContractError("handoff pending context is invalid")
    _text(pending["next_action"], "pending.next_action", 512)
    _text_list(pending["blockers"], "pending.blockers", 16)
    _text_list(pending["risks"], "pending.risks", 16)
    memory = payload["memory_projection"]
    if not isinstance(memory, dict) or set(memory) != {"local", "archive_refs", "openviking"}:
        raise ContractError("handoff memory projection is invalid")
    for field in memory:
        _text_list(memory[field], "memory_projection.%s" % field, 32)
    if payload["authorization"] != AUTHORIZATION:
        raise ContractError("handoff authorization is invalid")
    integrity = payload["integrity"]
    if not isinstance(integrity, dict) or set(integrity) != {"payload_digest", "source_digest"}:
        raise ContractError("handoff integrity is invalid")
    _digest_text(integrity["payload_digest"], "integrity.payload_digest")
    _digest_text(integrity["source_digest"], "integrity.source_digest")


def validate(root: Path, payload: Dict[str, Any], handoff_id: str) -> str:
    _validate_payload_shape(root, payload, handoff_id)
    integrity = payload["integrity"]
    if integrity["payload_digest"] != _payload_digest(payload):
        raise ContractError("handoff payload digest does not match")
    rollout_status = _verify_rollout(payload["source"]["rollout"])
    if rollout_status != "ready":
        return rollout_status
    evidence = _evidence_snapshot(root, [item["path"] for item in payload["source"]["evidence"]])
    if evidence != payload["source"]["evidence"]:
        return "changed"
    current = _source(root, _task_snapshot(root), evidence, payload["source"]["rollout"])
    return "ready" if integrity["source_digest"] == current["digest"] else "changed"


def _atomic_json(destination: Path, payload: Dict[str, Any]) -> None:
    base = destination.parent.parent
    if base.is_symlink():
        raise ContractError("session-handoffs directory is unsafe")
    base.mkdir(parents=True, exist_ok=True)
    os.chmod(base, 0o700)
    destination.parent.mkdir(exist_ok=False)
    os.chmod(destination.parent, 0o700)
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    except Exception:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        if destination.parent.exists() and not any(destination.parent.iterdir()):
            destination.parent.rmdir()
        raise


def emit(operation: str, status: str, reason: Optional[str] = None, **details: Any) -> None:
    result: Dict[str, Any] = {"operation": operation, "status": status, **details}
    if reason:
        result["reason"] = reason
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write")
    write.add_argument("--request", required=True, type=Path)
    write.add_argument("--explicit-user-request", action="store_true")
    check = sub.add_parser("validate")
    check.add_argument("--handoff", required=True)
    args = parser.parse_args()
    try:
        root = _root(str(args.project_root))
        if args.command == "validate":
            handoff_id, destination = _destination(root, handoff_path=args.handoff)
            relative = destination.relative_to(root).as_posix()
            if not destination.exists():
                emit("validate", "absent", handoff_path=relative, handoff_id=handoff_id)
                return 2
            _regular_file(destination, "handoff path")
            payload = load_json_file(destination, MAX_PAYLOAD_BYTES)
            status = validate(root, payload, handoff_id)
            emit("validate", status, handoff_path=relative, handoff_id=handoff_id)
            return 0 if status == "ready" else 2
        if not args.explicit_user_request:
            raise ContractError("write requires --explicit-user-request")
        request = _request(root, args.request)
        handoff_id = _handoff_id()
        _, destination = _destination(root, create_id=handoff_id)
        if destination.parent.exists():
            raise ContractError("handoff package already exists: %s" % handoff_id)
        payload = build(root, request, handoff_id)
        _atomic_json(destination, payload)
        emit("write", "ready", handoff_id=handoff_id, handoff_path=destination.relative_to(root).as_posix())
        return 0
    except (ContractError, OSError, subprocess.SubprocessError) as exc:
        emit(getattr(args, "command", "handoff"), "recovery_required", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
