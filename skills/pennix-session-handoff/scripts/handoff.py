#!/usr/bin/env python3
"""Create and validate an explicit-user-request-only session handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import (  # noqa: E402
    ContractError, SECRET_RE, LIFECYCLE_MODES, _text, _text_list, free_text, lifecycle_mode,
    load_json_file, safe_id, validate_attestation,
    validate_observation,
)


SCHEMA_VERSION = 6
SUPPORTED_SCHEMA_VERSIONS = {4, 5, 6}
KIND = "pennix-session-handoff"
PARSER_VERSION = "codex-jsonl-local-v1"
HANDOFFS = ".trellis/session-handoffs"
HANDOFF_NAME = "session-handoff.json"
HANDOFF_ID = re.compile(r"^\d{8}T\d{12}Z$")
AUTHORIZATION = {
    "source": "current_user_explicit_request",
    "attestation": "coordinator_asserted_not_runtime_verified",
}
LIFECYCLE_RUNTIME = ".trellis/.runtime/handoff-lifecycle"
ARCHIVE_RUNTIME = ".trellis/.runtime/handoff-archive"
LIFECYCLE_SCHEMA_VERSION = 2
LIFECYCLE_EVENT_KIND = "pennix-handoff-lifecycle-event"
SOURCE_STATES = {"unprepared", "prepared", "boundary_sealed", "pending", "archive_verified", "converged", "unavailable", "unsupported", "failed", "expired"}
TARGET_STATES = {"not_admitted", "admitted", "reconciled", "blocked", "disposed"}
RETENTION_STATES = {"none", "archive_eligible", "archived", "retained", "restored", "reopened", "purged"}
LIFECYCLE_ACTOR = "pennix-session-handoff"


def _root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    trellis = root / ".trellis"
    if not root.is_dir() or trellis.is_symlink() or not trellis.is_dir():
        raise ContractError("project root must contain a regular .trellis directory")
    return root


def _ownership_core_digest(path: Path) -> str:
    """Satisfy Trellis ownership's existing digest-only command contract."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(256 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
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


def _task_snapshot_at(root: Path, raw_path: str, expected: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    task_dir = _project_file(root, raw_path, "task path")
    if not task_dir.is_dir():
        raise ContractError("task directory is unavailable")
    task_json = task_dir / "task.json"
    if task_json.is_file():
        task_data = load_json_file(task_json, 64 * 1024)
        task_id = _text(task_data.get("id") or task_data.get("name"), "task.id", 256)
        status = _text(task_data.get("status"), "task.status", 64)
    elif expected is not None:
        task_id = _text(expected.get("id"), "task.id", 256)
        status = _text(expected.get("status"), "task.status", 64)
    else:
        raise ContractError("task.json is unavailable")
    return {"id": task_id, "path": raw_path, "status": status}


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
    snapshot = _task_snapshot_at(root, raw_path, selected)
    if snapshot["id"] != _text(selected.get("id"), "task.id", 256) or snapshot["status"] != _text(selected.get("status"), "task.status", 64):
        raise ContractError("active task changed while being captured")
    return snapshot


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
        if HANDOFFS + "/" not in line
        and ".trellis/session-handoff" not in line
        and ".trellis/.runtime/" not in line
    ]
    history = [line for line in run("log", "-n", "12", "--format=%H").splitlines() if line]
    return {
        "branch": branch,
        "head": head,
        "worktree_state": "dirty" if dirty_lines else "clean",
        "recent_commits": history,
    }


def _evidence_snapshot(root: Path, paths: Iterable[str]) -> list[Dict[str, Any]]:
    evidence: list[Dict[str, Any]] = []
    for relative in paths:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts or str(candidate).startswith(".trellis/.runtime/"):
            raise ContractError("evidence paths must be project-relative non-runtime paths")
        _regular_file(_project_file(root, relative, "evidence path"), "evidence path")
        evidence.append({"path": relative})
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


def _short_text(value: Any, maximum: Optional[int] = None) -> Optional[str]:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    if SECRET_RE.search(compact):
        return "[redacted: possible credential]"
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
    identifiers = re.findall(r"`([^`]+)`", text)
    identifiers += re.findall(r"\b(?:issue|task)\s*#?\d+\b", text, re.IGNORECASE)
    identifiers += re.findall(r"\b[a-z][a-z0-9]+(?:-[a-z0-9]+){1,}\b", text, re.IGNORECASE)
    values = [value.strip().lower() for value in paths + identifiers if value.strip()]
    return "|".join(sorted(set(values)) or []) or None


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
        capture_size = start.st_size
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
        compacted_spans: list[Dict[str, Any]] = []

        def keep(items: list[Dict[str, Any]], item: Dict[str, Any]) -> None:
            items.append(item)

        def count(items: Dict[str, int], key: str) -> None:
            items[key] = items.get(key, 0) + 1
        while offset < capture_size:
            remaining = capture_size - offset
            raw_line = handle.readline(remaining + 1)
            if not raw_line:
                break
            if not raw_line.endswith(b"\n") and offset + len(raw_line) < capture_size:
                raise ContractError("rollout contains an incomplete record before capture boundary")
            if not raw_line.endswith(b"\n"):
                omissions.append({"kind": "trailing_partial_record", "byte_start": offset, "bytes": len(raw_line)})
                break
            line_number += 1
            byte_start = offset
            offset += len(raw_line)
            if not raw_line.strip():
                continue
            if raw_line.rstrip(b"\r\n") and not raw_line.rstrip(b"\r\n").replace(b"\0", b""):
                omissions.append({
                    "kind": "nul_padding_record",
                    "line": line_number,
                    "byte_start": byte_start,
                    "byte_end": offset,
                    "bytes": len(raw_line),
                })
                continue
            try:
                record = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ContractError("rollout JSONL record is invalid at line %d" % line_number) from exc
            if not isinstance(record, dict):
                raise ContractError("rollout record is not an object at line %d" % line_number)
            record_count += 1
            record_type = str(record.get("type", "unknown"))
            payload = record.get("payload")
            source = {"line": line_number, "byte_start": byte_start, "byte_end": offset, "record_type": record_type}
            if isinstance(record.get("timestamp"), str):
                source["timestamp"] = _short_text(record["timestamp"], 128)
            payload_type = payload.get("type") if isinstance(payload, dict) else None
            if record_type == "compacted" or payload_type == "compacted":
                count(excluded, "compacted")
                compacted_spans.append({
                    "line": line_number,
                    "byte_start": byte_start,
                    "byte_end": offset,
                    "bytes": len(raw_line),
                })
                continue
            role, message_text = _event_message(record_type, payload)
            if role and message_text:
                event_index += 1
                keep(candidates, {"kind": role, "event_index": event_index, "text": message_text, "source": source})
                if role == "user":
                    topic = _topic_key(message_text)
                    if topic:
                        repeat_key = topic + "\0" + message_text
                        repeated[repeat_key] = repeated.get(repeat_key, 0) + 1
                        item: Dict[str, Any] = {"topic_key": topic, "state": "repeated" if repeated[repeat_key] > 1 else _timeline_state(message_text), "event_index": event_index, "summary": message_text, "source": source, "repeat_count": repeated[repeat_key]}
                        if topic in latest_by_topic:
                            item["supersedes_event_index"] = latest_by_topic[topic]
                        latest_by_topic[topic] = event_index
                        keep(timeline, item)
                continue
            if record_type != "response_item" or not isinstance(payload, dict):
                count(unknown, record_type)
                unknown_spans.append({"record_type": record_type, "line": line_number, "byte_start": byte_start, "byte_end": offset})
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
                if call_id:
                    tool_calls[call_id] = event_index + 1
                event_index += 1
                item = {"kind": "tool_call", "event_index": event_index, "tool": _short_text(payload.get("name"), 256), "source": source}
                if call_id:
                    item["call_id"] = call_id
                keep(candidates, item)
                continue
            if item_type in {"function_call_output", "custom_tool_call_output", "tool_result"}:
                call_id = _short_text(payload.get("call_id") or payload.get("id"), 256)
                if call_id:
                    tool_results[call_id] = event_index + 1
                event_index += 1
                item = {"kind": "tool_result", "event_index": event_index, "source": source}
                if call_id:
                    item["call_id"] = call_id
                keep(candidates, item)
                continue
            count(unknown, "response_item:%s" % item_type)
            unknown_spans.append({"record_type": "response_item:%s" % item_type, "line": line_number, "byte_start": byte_start, "byte_end": offset})
        capture_end = offset
        end = os.fstat(handle.fileno())
    if end.st_size < capture_end:
        raise ContractError("rollout source changed while being captured")
    coverage = {
        "source_bytes_at_capture": capture_size, "capture_end": capture_end, "record_count": record_count,
        "event_count": event_index, "excluded": excluded, "unknown": unknown, "omissions": omissions,
        "unknown_spans": unknown_spans,
        "compacted_spans": compacted_spans,
        "incomplete_tool_calls": sorted(set(tool_calls) ^ set(tool_results)),
    }
    return {
        "path": str(path), "session_id": session_id,
        "capture_end": capture_end, "record_count": record_count,
        "parser_version": PARSER_VERSION, "coverage": coverage, "conversation_candidates": candidates,
        "timeline": timeline,
    }


def _source(root: Path, task: Optional[Dict[str, str]], evidence: list[Dict[str, Any]], rollout: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task": task, "git": _git_snapshot(root), "evidence": evidence,
        "rollout_identity": {key: rollout[key] for key in ("path", "session_id", "capture_end", "record_count", "parser_version")},
    }


def _request(root: Path, path: Path) -> Dict[str, Any]:
    value = load_json_file(path, None)
    required = {"session_label", "facts", "evidence_paths", "next_action", "blockers", "risks", "validation", "rollout"}
    if not required.issubset(value) or set(value) - required - {"memory_projection"}:
        raise ContractError("handoff request fields are invalid")
    evidence_paths = _text_list(value["evidence_paths"], "evidence_paths")
    validation = value["validation"]
    if not isinstance(validation, list):
        raise ContractError("validation must be a list")
    normalized_validation = []
    for index, item in enumerate(validation):
        if not isinstance(item, dict) or set(item) != {"command", "result"}:
            raise ContractError("validation[%d] fields are invalid" % index)
        normalized_validation.append({"command": _text(item["command"], "validation[%d].command" % index), "result": _text(item["result"], "validation[%d].result" % index)})
    memory_projection = value.get("memory_projection", {})
    if not isinstance(memory_projection, dict) or set(memory_projection) - {"semantic_capsule", "local", "archive_refs", "openviking"}:
        raise ContractError("memory_projection fields are invalid")
    normalized = {
        "session_label": _text(value["session_label"], "session_label"), "facts": _text_list(value["facts"], "facts"),
        "evidence_paths": evidence_paths, "next_action": _text(value["next_action"], "next_action"),
        "blockers": _text_list(value["blockers"], "blockers"), "risks": _text_list(value["risks"], "risks"),
        "validation": normalized_validation, "rollout": _read_rollout_path(value["rollout"]),
        "memory_projection": {
            "semantic_capsule": free_text(memory_projection.get("semantic_capsule", ""), "memory_projection.semantic_capsule"),
            "local": _text_list(memory_projection.get("local", []), "memory_projection.local"),
            "archive_refs": _text_list(memory_projection.get("archive_refs", []), "memory_projection.archive_refs"),
            "openviking": _text_list(memory_projection.get("openviking", []), "memory_projection.openviking"),
        },
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
        "project": {"name": root.name},
        "work_context": {"task": task},
        "source": {"session_label": request["session_label"], "git": source["git"], "evidence": evidence, "rollout": rollout},
        "verified": {"facts": request["facts"], "validation": request["validation"]},
        "conversation": {"candidates": rollout["conversation_candidates"], "timeline": rollout["timeline"], "coverage": rollout["coverage"]},
        "pending": {"next_action": request["next_action"], "blockers": request["blockers"], "risks": request["risks"]},
        "memory_projection": request["memory_projection"], "authorization": dict(AUTHORIZATION),
    }
    return payload


def _validate_payload_shape(root: Path, payload: Dict[str, Any], handoff_id: str) -> None:
    legacy = payload.get("schema_version") in {4, 5}
    expected = {"schema_version", "kind", "handoff_id", "created_at", "project", "work_context", "source", "verified", "conversation", "pending", "memory_projection", "authorization"}
    if legacy:
        expected.add("integrity")
    if set(payload) != expected or payload["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS or payload["kind"] != KIND:
        raise ContractError("handoff schema is unsupported")
    if payload["handoff_id"] != handoff_id or not HANDOFF_ID.fullmatch(handoff_id):
        raise ContractError("handoff id does not match package path")
    _text(payload["created_at"], "created_at", 128)
    if not isinstance(payload["project"], dict) or payload["project"].get("name") != root.name:
        raise ContractError("handoff project identity is invalid")
    context = payload["work_context"]
    if not isinstance(context, dict) or set(context) != {"task"}:
        raise ContractError("handoff work context is invalid")
    task = context["task"]
    if task is not None and (not isinstance(task, dict) or not {"id", "path", "status"}.issubset(task)):
        raise ContractError("handoff task is invalid")
    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"session_label", "git", "evidence", "rollout"}:
        raise ContractError("handoff source is invalid")
    _text(source["session_label"], "source.session_label", 128)
    if not isinstance(source["evidence"], list):
        raise ContractError("handoff evidence is invalid")
    for item in source["evidence"]:
        if not isinstance(item, dict) or set(item) != {"path"}:
            if not legacy or not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
                raise ContractError("handoff evidence item is invalid")
        if not isinstance(item, dict) or "path" not in item:
            raise ContractError("handoff evidence item is invalid")
        _project_file(root, _text(item["path"], "evidence.path", 1024), "evidence path")
    rollout = source["rollout"]
    rollout_expected = {"path", "session_id", "capture_end", "record_count", "parser_version", "coverage", "conversation_candidates", "timeline"}
    if legacy:
        rollout_expected |= {"device", "inode", "prefix_sha256"}
    if not isinstance(rollout, dict) or set(rollout) != rollout_expected:
        raise ContractError("handoff rollout descriptor is invalid")
    _text(rollout["path"], "rollout.path", 4096)
    if rollout["session_id"] is not None:
        _text(rollout["session_id"], "rollout.session_id", 256)
    for field in ("capture_end", "record_count"):
        if not isinstance(rollout[field], int) or rollout[field] < 0:
            raise ContractError("rollout.%s is invalid" % field)
    if rollout["parser_version"] != PARSER_VERSION:
        raise ContractError("rollout parser version is unsupported")
    if not isinstance(rollout["coverage"], dict) or not isinstance(rollout["conversation_candidates"], list) or not isinstance(rollout["timeline"], list):
        raise ContractError("rollout summary is invalid")
    verified = payload["verified"]
    if not isinstance(verified, dict) or set(verified) != {"facts", "validation"}:
        raise ContractError("handoff verified context is invalid")
    _text_list(verified["facts"], "verified.facts")
    if not isinstance(verified["validation"], list):
        raise ContractError("handoff validation is invalid")
    pending = payload["pending"]
    if not isinstance(pending, dict) or set(pending) != {"next_action", "blockers", "risks"}:
        raise ContractError("handoff pending context is invalid")
    _text(pending["next_action"], "pending.next_action")
    _text_list(pending["blockers"], "pending.blockers")
    _text_list(pending["risks"], "pending.risks")
    memory = payload["memory_projection"]
    if not isinstance(memory, dict):
        raise ContractError("handoff memory projection is invalid")
    if payload["schema_version"] == 4:
        if set(memory) != {"local", "archive_refs", "openviking"}:
            raise ContractError("handoff memory projection is invalid")
    else:
        if set(memory) != {"semantic_capsule", "local", "archive_refs", "openviking"}:
            raise ContractError("handoff memory projection is invalid")
        free_text(memory["semantic_capsule"], "memory_projection.semantic_capsule")
    for field in ("local", "archive_refs", "openviking"):
        _text_list(memory[field], "memory_projection.%s" % field)
    if payload["authorization"] != AUTHORIZATION:
        raise ContractError("handoff authorization is invalid")
def validate(root: Path, payload: Dict[str, Any], handoff_id: str) -> str:
    _validate_payload_shape(root, payload, handoff_id)
    return "ready"


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
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        if destination.parent.exists() and not any(destination.parent.iterdir()):
            destination.parent.rmdir()
        raise


def _lifecycle_path(root: Path, handoff_id: str) -> Path:
    safe_id(handoff_id, "handoff_id")
    runtime = root / ".trellis" / ".runtime"
    base = root / LIFECYCLE_RUNTIME
    for path in (runtime, base):
        if path.is_symlink():
            raise ContractError("handoff lifecycle directory is unsafe")
    return base / (handoff_id + ".jsonl")


def _archive_path(root: Path, handoff_id: str) -> Path:
    safe_id(handoff_id, "handoff_id")
    runtime = root / ".trellis" / ".runtime"
    base = root / ARCHIVE_RUNTIME
    for path in (runtime, base):
        if path.is_symlink():
            raise ContractError("handoff archive directory is unsafe")
    return base / handoff_id


def _core(root: Path, handoff_path: str) -> tuple[str, Path, Dict[str, Any]]:
    handoff_id, destination = _destination(root, handoff_path=handoff_path)
    _regular_file(destination, "handoff path")
    payload = load_json_file(destination, None)
    if validate(root, payload, handoff_id) != "ready":
        raise ContractError("handoff core is not ready")
    return handoff_id, destination, payload


def _read_paired_prompt(root: Path, handoff_path: str) -> None:
    _, core = _destination(root, handoff_path=handoff_path)
    prompt = _regular_file(core.with_name("session-handoff-prompt.md"), "paired handoff prompt")
    try:
        prompt.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError("paired handoff prompt is unreadable") from exc


def _event_shape(event: Any, handoff_id: str) -> Dict[str, Any]:
    if not isinstance(event, dict):
        raise ContractError("lifecycle event schema is invalid")
    legacy = event.get("schema_version") == 1
    expected = {
        "schema_version", "kind", "handoff_id", "event_type", "source_status", "target_status",
        "retention_status", "observed_at", "actor", "evidence_refs",
    }
    if legacy:
        expected |= {"core_digest", "event_id", "prev_event_digest", "event_digest"}
    if set(event) != expected or event["schema_version"] not in {1, LIFECYCLE_SCHEMA_VERSION}:
        raise ContractError("lifecycle event schema is invalid")
    if event["kind"] != LIFECYCLE_EVENT_KIND or event["handoff_id"] != handoff_id:
        raise ContractError("lifecycle event identity is invalid")
    _text(event["event_type"], "event.event_type")
    for field, values in (("source_status", SOURCE_STATES), ("target_status", TARGET_STATES), ("retention_status", RETENTION_STATES)):
        value = _text(event[field], "event.%s" % field)
        if value not in values:
            raise ContractError("event.%s is invalid" % field)
    _text(event["observed_at"], "event.observed_at")
    if event["actor"] != LIFECYCLE_ACTOR:
        raise ContractError("event.actor is invalid")
    _text_list(event["evidence_refs"], "event.evidence_refs")
    if SECRET_RE.search(json.dumps(event, ensure_ascii=False)):
        raise ContractError("lifecycle event contains a possible credential or secret")
    return event


def _transition(axis: str, old: str, new: str) -> bool:
    if old == new:
        return True
    transitions = {
        "source": {
            "unprepared": {"prepared", "failed"},
            "prepared": {"boundary_sealed", "pending", "unsupported", "unavailable", "failed"},
            "boundary_sealed": {"archive_verified", "converged", "failed"},
            "archive_verified": {"converged", "failed"},
            "pending": {"boundary_sealed", "archive_verified", "converged", "unsupported", "unavailable", "failed"},
            "unsupported": {"boundary_sealed", "pending", "archive_verified", "converged", "failed"},
            "unavailable": {"boundary_sealed", "pending", "archive_verified", "converged", "failed"},
            "converged": {"expired"}, "failed": {"failed"}, "expired": set(),
        },
        "target": {"not_admitted": {"admitted", "reconciled", "blocked"}, "admitted": {"reconciled", "blocked", "disposed"}, "reconciled": {"disposed"}, "blocked": {"admitted", "reconciled", "disposed"}, "disposed": set()},
        "retention": {"none": {"archive_eligible"}, "archive_eligible": {"archived"}, "archived": {"retained", "restored", "reopened", "purged"}, "retained": {"restored", "reopened", "purged"}, "restored": {"reopened", "purged"}, "reopened": {"purged"}, "purged": {"restored"}},
    }
    return new in transitions[axis].get(old, set())


def _read_events(path: Path, handoff_id: str) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    _regular_file(path, "lifecycle receipt")
    events: list[Dict[str, Any]] = []
    states = {"source": "unprepared", "target": "not_admitted", "retention": "none"}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ContractError("lifecycle receipt is unreadable") from exc
    for raw in lines:
        if not raw:
            raise ContractError("lifecycle receipt contains an invalid line")
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ContractError("lifecycle receipt contains invalid JSON") from exc
        event = _event_shape(event, handoff_id)
        for axis, key in (("source", "source_status"), ("target", "target_status"), ("retention", "retention_status")):
            if not _transition(axis, states[axis], event[key]):
                raise ContractError("lifecycle %s transition is invalid" % axis)
        states = {"source": event["source_status"], "target": event["target_status"], "retention": event["retention_status"]}
        events.append(event)
    return events


def _state(events: list[Dict[str, Any]]) -> dict[str, str]:
    if not events:
        return {"source": "unprepared", "target": "not_admitted", "retention": "none"}
    event = events[-1]
    return {"source": event["source_status"], "target": event["target_status"], "retention": event["retention_status"]}


def _prepared_mode(events: list[Dict[str, Any]]) -> str:
    prepare = next((event for event in events if event["event_type"] == "prepare"), None)
    if prepare is None:
        raise ContractError("handoff lifecycle is not prepared")
    mode = next((ref.split("=", 1)[1] for ref in prepare["evidence_refs"] if ref.startswith("mode=")), None)
    if mode is None:
        raise ContractError("handoff lifecycle mode is unavailable")
    return lifecycle_mode(mode)


def _reconciled_admit_target(events: list[Dict[str, Any]]) -> Optional[str]:
    targets: list[str] = []
    for event in events:
        if event["event_type"] != "admit" or event["target_status"] != "reconciled":
            continue
        refs = [reference.removeprefix("target=") for reference in event["evidence_refs"] if reference.startswith("target=")]
        if len(refs) != 1:
            raise ContractError("reconciled admission target is invalid")
        targets.append(refs[0])
    if len(targets) > 1:
        raise ContractError("handoff asset has multiple successful consumers")
    return targets[0] if targets else None


def _source_ready(mode: str, state: dict[str, str]) -> bool:
    required = {
        "core_only": "prepared",
        "capsule_required": "boundary_sealed",
        "archive_required": "archive_verified",
        "convergence_required": "converged",
    }[mode]
    if mode == "core_only":
        return state["source"] in {"prepared", "boundary_sealed", "archive_verified", "converged"}
    return state["source"] == required


def _append_event(root: Path, handoff_id: str, event_type: str, desired: dict[str, str], evidence_refs: list[str]) -> dict[str, Any]:
    path = _lifecycle_path(root, handoff_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    # ponytail: one per-handoff advisory lock; upgrade to a lock service only if concurrent writers become measurable.
    with path.open("a+", encoding="utf-8") as handle:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError) as exc:
            raise ContractError("lifecycle lock unavailable") from exc
        handle.seek(0)
        events = _read_events(path, handoff_id)
        current = _state(events)
        if event_type == "prepare":
            existing = next((event for event in events if event["event_type"] == "prepare"), None)
            if existing is not None:
                if _prepared_mode(events) != next((ref.removeprefix("mode=") for ref in evidence_refs if ref.startswith("mode=")), None):
                    raise ContractError("handoff lifecycle mode is immutable")
                return {"status": "idempotent", "state": current}
        if event_type == "admit" and desired["target"] == "reconciled":
            target_refs = [reference.removeprefix("target=") for reference in evidence_refs if reference.startswith("target=")]
            if len(target_refs) != 1:
                raise ContractError("admission target is invalid")
            successful_target = _reconciled_admit_target(events)
            if successful_target is not None:
                if successful_target == target_refs[0]:
                    return {"status": "idempotent", "state": current, "target": successful_target}
                raise ContractError("handoff asset has already been consumed by another target")
        if event_type != "admit" and current == desired and any(old["event_type"] == event_type and old["evidence_refs"] == evidence_refs for old in events):
            return {"status": "idempotent", "state": current}
        for axis in ("source", "target", "retention"):
            if not _transition(axis, current[axis], desired[axis]):
                raise ContractError("lifecycle %s transition is invalid" % axis)
        event: Dict[str, Any] = {
            "schema_version": LIFECYCLE_SCHEMA_VERSION, "kind": LIFECYCLE_EVENT_KIND,
            "handoff_id": handoff_id,
            "event_type": event_type, "source_status": desired["source"], "target_status": desired["target"],
            "retention_status": desired["retention"], "observed_at": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
            "actor": LIFECYCLE_ACTOR, "evidence_refs": evidence_refs,
        }
        encoded = json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n"
        handle.seek(0, 2)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
        return {"status": "recorded", "state": desired}


def _task_current(root: Path) -> dict[str, Any]:
    script = _regular_file(root / ".trellis/scripts/task.py", "task.py")
    result = subprocess.run([sys.executable, str(script), "current", "--json"], cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
    if result.returncode not in (0, 1) or result.stderr:
        raise ContractError("task.py current failed")
    try:
        value = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("task.py current returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("task.py current returned invalid JSON")
    return value


def _ownership_task(payload: dict[str, Any]) -> tuple[str, str]:
    task = payload["work_context"].get("task")
    if not isinstance(task, dict):
        raise ContractError("handoff has no task ownership to transfer")
    task_id = safe_id(task.get("id"), "handoff task id")
    task_path = _text(task.get("path"), "handoff task path", 1024)
    if not task_path.startswith(".trellis/tasks/") or ".." in Path(task_path).parts:
        raise ContractError("handoff task path is unsafe")
    return task_id, task_path


def _direct_session_id(root: Path) -> str:
    source = _task_current(root).get("source")
    if not isinstance(source, str) or not source.startswith("session:"):
        raise ContractError("Trellis did not expose a direct session identity")
    return safe_id(source.removeprefix("session:"), "direct session id")


def _ownership_call(root: Path, operation: str, task_id: str, handoff_id: str, core_digest: str, extra: list[str], *, explicit: bool) -> dict[str, Any]:
    script = _regular_file(root / ".trellis/scripts/task.py", "task.py")
    command = [
        sys.executable, str(script), "ownership", operation,
        "--task-id", task_id, "--handoff-id", handoff_id, "--core-digest", core_digest,
        *extra,
    ]
    if explicit:
        command.append("--explicit-user-request")
    result = subprocess.run(
        command, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=20, check=False,
    )
    try:
        value = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Trellis ownership returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("Trellis ownership returned invalid JSON")
    if SECRET_RE.search(json.dumps(value, ensure_ascii=False)):
        raise ContractError("Trellis ownership returned unsafe data")
    if result.returncode:
        reason = _text(value.get("reason"), "ownership failure", 512) if value.get("reason") else "unknown failure"
        raise ContractError("Trellis ownership %s withheld: %s" % (operation, reason))
    return value


def _ownership_event(root: Path, handoff_id: str, operation: str, result: dict[str, Any]) -> dict[str, Any]:
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    if not events:
        raise ContractError("handoff lifecycle is not prepared")
    state = _state(events)
    refs = [
        "ownership_status=" + _text(result.get("status"), "ownership.status", 32),
        "ownership_generation=" + str(result.get("generation")),
    ]
    receipt = _append_event(
        root, handoff_id, "ownership_" + operation,
        {"source": state["source"], "target": state["target"], "retention": state["retention"]},
        refs,
    )
    return {"ownership": result, "lifecycle": receipt}


def _ownership_gate(root: Path, mode: str, state: dict[str, str], observation: Optional[str]) -> None:
    if mode in {"archive_required", "convergence_required"} and observation != "observed":
        raise ContractError("ownership retirement requires an observed archive for %s" % mode)
    if mode in {"archive_required", "convergence_required"} and state["source"] not in {"archive_verified", "converged"}:
        raise ContractError("handoff source archive is not verified")
    if mode == "convergence_required" and state["source"] != "converged":
        raise ContractError("handoff source convergence is not verified")


def ownership_operation(root: Path, operation: str, handoff_path: str, *, explicit: bool, archive_observation: Optional[str] = None, expected_generation: Optional[int] = None) -> dict[str, Any]:
    handoff_id, core, payload = _core(root, handoff_path)
    core_digest = _ownership_core_digest(core)
    task_id, task_path = _ownership_task(payload)
    if operation == "status":
        result = _ownership_call(root, operation, task_id, handoff_id, core_digest, ["--json"], explicit=False)
        return {"handoff_id": handoff_id, "ownership": result}
    if not explicit:
        raise ContractError("ownership writes require --explicit-user-request")
    extra: list[str] = []
    if operation == "quiesce":
        current = _task_current(root).get("current_task")
        if not isinstance(current, dict) or current.get("id") != task_id or current.get("dir") != task_path:
            raise ContractError("source task is not the direct current task")
        extra += ["--task", task_path, "--source-session-id", _direct_session_id(root)]
    else:
        if expected_generation is None:
            raise ContractError("expected ownership generation is required")
        extra += ["--expected-generation", str(expected_generation)]
        if operation == "claim":
            extra += ["--task", task_path]
        if operation == "retire":
            observation = archive_observation or "not_required"
            events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
            _ownership_gate(root, _prepared_mode(events), _state(events), observation)
            extra += ["--archive-observation", observation]
    result = _ownership_call(root, operation, task_id, handoff_id, core_digest, extra, explicit=True)
    receipt = _ownership_event(root, handoff_id, operation, result)
    return {"handoff_id": handoff_id, **receipt}


def _archive_snapshot(root: Path, archive: Path, handoff_id: str) -> list[str]:
    if not archive.is_dir() or archive.is_symlink():
        raise ContractError("handoff archive is unavailable")
    names = {path.name for path in archive.iterdir()}
    if names != {HANDOFF_NAME, "session-handoff-prompt.md"}:
        raise ContractError("handoff archive must contain a core/prompt pair")
    core = _regular_file(archive / HANDOFF_NAME, "archived handoff")
    payload = load_json_file(core, None)
    _validate_payload_shape(root, payload, handoff_id)
    refs = ["archive=" + handoff_id]
    prompt = _regular_file(archive / "session-handoff-prompt.md", "archived prompt")
    try:
        prompt.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError("archived prompt is unreadable") from exc
    return refs


def _archive_copy(root: Path, handoff_id: str, core: Path) -> list[str]:
    archive = _archive_path(root, handoff_id)
    if archive.exists():
        return _archive_snapshot(root, archive, handoff_id)
    parent = archive.parent
    parent.mkdir(parents=True, exist_ok=True)
    os.chmod(parent, 0o700)
    temporary = Path(tempfile.mkdtemp(prefix="." + handoff_id + ".", dir=parent))
    try:
        os.chmod(temporary, 0o700)
        shutil.copyfile(core, temporary / HANDOFF_NAME)
        os.chmod(temporary / HANDOFF_NAME, 0o600)
        prompt = _regular_file(core.parent / "session-handoff-prompt.md", "handoff prompt")
        shutil.copyfile(prompt, temporary / "session-handoff-prompt.md")
        os.chmod(temporary / "session-handoff-prompt.md", 0o600)
        _archive_snapshot(root, temporary, handoff_id)
        directory_fd = os.open(temporary, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        os.replace(temporary, archive)
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return _archive_snapshot(root, archive, handoff_id)


def _restore_copy(source: Path, destination: Path) -> None:
    _regular_file(source, "archived restore source")
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
        shutil.copyfile(source, temporary)
        os.chmod(temporary, 0o600)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _lifecycle_result(operation: str, handoff_id: str, result: dict[str, Any]) -> None:
    emit(operation, result["status"], handoff_id=handoff_id, **{key: value for key, value in result.items() if key != "status"})


def lifecycle_prepare(root: Path, handoff_path: str, mode: str) -> tuple[str, dict[str, Any]]:
    handoff_id, _, _ = _core(root, handoff_path)
    selected_mode = lifecycle_mode(mode)
    return handoff_id, _append_event(root, handoff_id, "prepare", {"source": "prepared", "target": "not_admitted", "retention": "none"}, ["mode=" + selected_mode])


def lifecycle_finalize(root: Path, handoff_path: str, observation_path: str) -> tuple[str, dict[str, Any]]:
    handoff_id, _, payload = _core(root, handoff_path)
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    if not events:
        raise ContractError("handoff lifecycle is not prepared")
    mode = _prepared_mode(events)
    observation = validate_observation(load_json_file(_project_file(root, observation_path, "observation path")))
    status = "pending"
    if observation["availability"] == "unsupported":
        status = "unsupported"
    elif observation["availability"] == "unavailable":
        status = "unavailable"
    elif observation["boundary"]["status"] == "sealed":
        status = "boundary_sealed"
        if mode in {"capsule_required", "archive_required", "convergence_required"}:
            if observation["capsule"]["status"] != "verified" or not observation["capsule"]["proof_ref"]:
                status = "pending"
            elif mode in {"archive_required", "convergence_required"}:
                source_session = payload["source"]["rollout"].get("session_id")
                if (
                    source_session is None
                    or observation["source_session"]["status"] != "verified"
                    or observation["source_session"]["identity"] != source_session
                    or observation["archive"]["status"] != "verified"
                    or not observation["archive"]["proof_ref"]
                ):
                    status = "pending"
                else:
                    status = "archive_verified"
                    if mode == "convergence_required":
                        if observation["task"]["status"] == "completed" and observation["task"]["completion_artifact"] and observation["memory"]["status"] == "verified" and observation["memory"]["proof_ref"]:
                            status = "converged"
                        else:
                            status = "pending"
    if status == "pending" and _state(events)["source"] in {"boundary_sealed", "archive_verified", "converged"}:
        status = _state(events)["source"]
    evidence = ["observation=" + observation_path]
    result = _append_event(root, handoff_id, "finalize", {"source": status, "target": _state(events)["target"], "retention": _state(events)["retention"]}, evidence)
    return handoff_id, result


def lifecycle_admit(root: Path, handoff_path: str, attestation_path: str) -> tuple[str, dict[str, Any]]:
    handoff_id, _, payload = _core(root, handoff_path)
    _read_paired_prompt(root, handoff_path)
    attestation = validate_attestation(load_json_file(_project_file(root, attestation_path, "attestation path")))
    rollout_session = payload["source"]["rollout"].get("session_id")
    if rollout_session is not None and attestation["target_source"] == "session:" + rollout_session:
        raise ContractError("target source cannot reuse the handoff source session id")
    current = _task_current(root)
    if current.get("source") != attestation["target_source"]:
        raise ContractError("target source is not the current direct session source")
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    current_state = _state(events)
    if not events:
        raise ContractError("handoff lifecycle is not prepared")
    source_ready = _source_ready(_prepared_mode(events), current_state)
    if not source_ready or not (attestation["prompt_read"] and attestation["trellis_started"] and attestation["facts_reconciled"]):
        target_status = "blocked"
    else:
        target_status = "reconciled"
    target_source = attestation["target_source"]
    successful_target = _reconciled_admit_target(events)
    if successful_target is not None:
        if target_source == successful_target:
            return handoff_id, {"status": "idempotent", "state": current_state, "target": target_source}
        raise ContractError("handoff asset has already been consumed by another target")
    retention_status = "archive_eligible" if target_status == "reconciled" else "none"
    result = _append_event(root, handoff_id, "admit", {"source": current_state["source"], "target": target_status, "retention": retention_status}, ["target=" + target_source])
    return handoff_id, result


def lifecycle_retention(root: Path, action: str, handoff_path: str, confirmation: str) -> tuple[str, dict[str, Any]]:
    handoff_id, core_path = _destination(root, handoff_path=handoff_path)
    if confirmation != handoff_id:
        raise ContractError("exact handoff id confirmation is required")
    if action == "restore":
        archive = _archive_path(root, handoff_id)
        archived_core = _regular_file(archive / HANDOFF_NAME, "archived handoff")
        archived_payload = load_json_file(archived_core, None)
        _validate_payload_shape(root, archived_payload, handoff_id)
        core = core_path
    else:
        handoff_id, core, _ = _core(root, handoff_path)
    receipt = _lifecycle_path(root, handoff_id)
    events = _read_events(receipt, handoff_id)
    state = _state(events)
    if action == "archive":
        if state["retention"] != "archive_eligible":
            raise ContractError("handoff is not archive eligible")
        refs = _archive_copy(root, handoff_id, core)
        result = _append_event(root, handoff_id, "archive", {"source": state["source"], "target": state["target"], "retention": "archived"}, refs)
    elif action == "restore":
        archive = _archive_path(root, handoff_id)
        refs = _archive_snapshot(root, archive, handoff_id)
        archived_core = archive / HANDOFF_NAME
        if not core.exists():
            core.parent.mkdir(parents=True, exist_ok=True)
            _restore_copy(archived_core, core)
        prompt = archive / "session-handoff-prompt.md"
        canonical_prompt = core.parent / "session-handoff-prompt.md"
        if not canonical_prompt.exists():
            _restore_copy(prompt, canonical_prompt)
        result = _append_event(root, handoff_id, "restore", {"source": state["source"], "target": state["target"], "retention": "restored"}, refs)
    elif action == "reopen":
        if state["retention"] not in {"archived", "retained", "restored"}:
            raise ContractError("handoff is not reopenable")
        refs = _archive_snapshot(root, _archive_path(root, handoff_id), handoff_id)
        result = _append_event(root, handoff_id, "reopen", {"source": state["source"], "target": state["target"], "retention": "reopened"}, refs)
    elif action == "purge":
        if state["retention"] not in {"archived", "retained", "restored", "reopened"}:
            raise ContractError("handoff is not purgeable")
        refs = _archive_snapshot(root, _archive_path(root, handoff_id), handoff_id)
        _append_event(root, handoff_id, "purge_intent", {"source": state["source"], "target": state["target"], "retention": state["retention"]}, refs)
        core.unlink(missing_ok=True)
        (core.parent / "session-handoff-prompt.md").unlink(missing_ok=True)
        directory_fd = os.open(core.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        result = _append_event(root, handoff_id, "purge", {"source": state["source"], "target": state["target"], "retention": "purged"}, refs)
    else:
        raise ContractError("retention action is unsupported")
    return handoff_id, result


def lifecycle_status(root: Path, handoff_path: str) -> dict[str, Any]:
    handoff_id, destination = _destination(root, handoff_path=handoff_path)
    if destination.exists():
        handoff_id, _, _ = _core(root, handoff_path)
    else:
        _archive_snapshot(root, _archive_path(root, handoff_id), handoff_id)
    path = _lifecycle_path(root, handoff_id)
    if not path.exists():
        return {"status": "absent", "handoff_id": handoff_id}
    events = _read_events(path, handoff_id)
    state = _state(events)
    mode = _prepared_mode(events)
    source_ready = _source_ready(mode, state)
    return {"status": "ready" if source_ready else "pending", "handoff_id": handoff_id, "mode": mode, "state": state}


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
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--handoff", required=True)
    prepare.add_argument("--mode", default="core_only", choices=sorted(LIFECYCLE_MODES))
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--handoff", required=True)
    finalize.add_argument("--observation", required=True)
    admit = sub.add_parser("admit")
    admit.add_argument("--handoff", required=True)
    admit.add_argument("--attestation", required=True)
    status = sub.add_parser("status")
    status.add_argument("--handoff", required=True)
    ownership = sub.add_parser("ownership")
    ownership_sub = ownership.add_subparsers(dest="ownership_command", required=True)
    for name in ("quiesce", "seal", "retire", "claim", "consume", "archive", "status"):
        command = ownership_sub.add_parser(name)
        command.add_argument("--handoff", required=True)
        if name == "retire":
            command.add_argument("--archive-observation", choices=("not_required", "observed"), default="not_required")
        if name in {"seal", "retire", "claim", "consume", "archive"}:
            command.add_argument("--expected-generation", required=True, type=int)
        if name != "status":
            command.add_argument("--explicit-user-request", action="store_true")
    retention = sub.add_parser("retention")
    retention.add_argument("action_positional", nargs="?", choices=("archive", "restore", "reopen", "purge"))
    retention.add_argument("--action", dest="action_option", choices=("archive", "restore", "reopen", "purge"))
    retention.add_argument("--handoff", required=True)
    retention.add_argument("--confirm-handoff-id", required=True)
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
            payload = load_json_file(destination, None)
            status = validate(root, payload, handoff_id)
            emit("validate", status, handoff_path=relative, handoff_id=handoff_id)
            return 0 if status == "ready" else 2
        if args.command == "prepare":
            handoff_id, result = lifecycle_prepare(root, args.handoff, args.mode)
            _lifecycle_result("prepare", handoff_id, result)
            return 0
        if args.command == "finalize":
            handoff_id, result = lifecycle_finalize(root, args.handoff, args.observation)
            _lifecycle_result("finalize", handoff_id, result)
            return 0
        if args.command == "admit":
            handoff_id, result = lifecycle_admit(root, args.handoff, args.attestation)
            _lifecycle_result("admit", handoff_id, result)
            return 0
        if args.command == "status":
            result = lifecycle_status(root, args.handoff)
            status = result.pop("status")
            emit("status", status, **result)
            return 0 if status in {"ready", "absent"} else 2
        if args.command == "ownership":
            result = ownership_operation(
                root, args.ownership_command, args.handoff,
                explicit=getattr(args, "explicit_user_request", False),
                archive_observation=getattr(args, "archive_observation", None),
                expected_generation=getattr(args, "expected_generation", None),
            )
            emit("ownership", "recorded", **result)
            return 0
        if args.command == "retention":
            action = args.action_positional or args.action_option
            if action is None:
                raise ContractError("retention action is required")
            handoff_id, result = lifecycle_retention(root, action, args.handoff, args.confirm_handoff_id)
            _lifecycle_result("retention", handoff_id, result)
            return 0
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
