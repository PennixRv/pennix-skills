#!/usr/bin/env python3
"""Create and validate an explicit-user-request-only session handoff."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import (  # noqa: E402
    ContractError, contains_secret, redact_text, LIFECYCLE_MODES, TARGET_SOURCE_RE, _text, _text_list, _fields, _integer, lifecycle_mode,
    load_json_file, safe_id, validate_attestation,
    validate_observation,
)
import handoff_storage as storage  # noqa: E402


SCHEMA_VERSION = 12
KIND = "pennix-session-handoff"
PARSER_VERSION = "codex-jsonl-local-v1"
HANDOFFS = ".trellis/session-handoffs"
HANDOFF_NAME = "session-handoff.json"
HISTORY_NAME = "session-handoff-history.jsonl"
HISTORY_TYPES = {"candidate", "timeline", "omission", "unknown_span", "compacted_span", "count", "incomplete_tool_call"}
HANDOFF_ID = re.compile(r"^\d{8}T\d{12}Z$")
AUTHORIZATION = {
    "source": "current_user_explicit_request",
    "attestation": "coordinator_asserted_not_runtime_verified",
}
LIFECYCLE_RUNTIME = ".trellis/.runtime/handoff-lifecycle"
ARCHIVE_RUNTIME = ".trellis/.runtime/handoff-archive"
LIFECYCLE_SCHEMA_VERSION = 3
LIFECYCLE_EVENT_KIND = "pennix-handoff-lifecycle-event"
CONSUMPTION_STEPS = ("core_view_read", "prompt_read", "trellis_started", "facts_reconciled")
CR_OBSERVATION_STATES = {"ready", "absent", "stale", "withheld", "unavailable"}
SOURCE_STATES = {"unprepared", "prepared", "boundary_sealed", "pending", "unavailable", "unsupported", "failed", "expired"}
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
        task_data = load_json_file(task_json)
        task_id = _text(task_data.get("id") or task_data.get("name"), "task.id")
        status = _text(task_data.get("status"), "task.status")
    elif expected is not None:
        task_id = _text(expected.get("id"), "task.id")
        status = _text(expected.get("status"), "task.status")
    else:
        raise ContractError("task.json is unavailable")
    return {"id": task_id, "path": raw_path, "status": status}


def _task_snapshot(root: Path) -> Optional[Dict[str, Any]]:
    current = _task_current(root)
    selected = current["current_task"]
    if selected is None:
        return None
    if not isinstance(selected, dict):
        raise ContractError("task.py current returned an invalid task")
    raw_path = _text(selected.get("dir"), "task.dir")
    task_path = Path(raw_path)
    if task_path.is_absolute() or ".." in task_path.parts or not raw_path.startswith(".trellis/tasks/"):
        raise ContractError("active task path is unsafe")
    snapshot = _task_snapshot_at(root, raw_path, selected)
    if snapshot["id"] != _text(selected.get("id"), "task.id") or snapshot["status"] != _text(selected.get("status"), "task.status"):
        raise ContractError("active task changed while being captured")
    snapshot["continuity"] = _continuity_snapshot(root, snapshot)
    return snapshot


def _continuity_call(root: Path, action: str, *arguments: str) -> Dict[str, Any]:
    script = _regular_file(root / ".trellis/scripts/task.py", "task.py")
    result = subprocess.run(
        [sys.executable, str(script), "continuity", action, *arguments], cwd=root,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=20, check=False,
    )
    try:
        value = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Trellis continuity returned invalid JSON") from exc
    if not isinstance(value, dict) or contains_secret(value):
        raise ContractError("Trellis continuity returned unsafe data")
    if result.returncode and value.get("status") != "withheld":
        reason = _text(value.get("reason"), "continuity failure") if value.get("reason") else "unknown failure"
        raise ContractError("Trellis continuity %s withheld: %s" % (action, reason))
    return value


def _continuity_observation(root: Path, task: Optional[Dict[str, str]]) -> Dict[str, Any]:
    observed_at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if task is None:
        return {"cr_status": "absent", "cr_source_digest": None, "cr_observed_at": observed_at, "cr_observation_state": "absent", "current": None}
    try:
        observed = _continuity_call(root, "show")
    except (OSError, subprocess.TimeoutExpired, ContractError):
        return {"cr_status": None, "cr_source_digest": None, "cr_observed_at": observed_at, "cr_observation_state": "unavailable", "current": None}

    status = observed.get("status")
    if status not in {"ready", "absent", "stale", "withheld"}:
        status = None
        state = "unavailable"
        digest = None
        current = None
    elif status == "withheld":
        state = "withheld"
        digest = observed.get("source_digest")
        current = observed.get("current")
    else:
        state = status
        digest = observed.get("source_digest")
        current = observed.get("current")
        current_task = current.get("task") if isinstance(current, dict) else None
        if (
            not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not isinstance(current_task, dict)
            or any(current_task.get(key) != task[key] for key in ("id", "path", "status"))
        ):
            state = "withheld"

    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        digest = None
    if not isinstance(current, dict):
        current = None
    return {
        "cr_status": status,
        "cr_source_digest": digest,
        "cr_observed_at": observed_at,
        "cr_observation_state": state,
        "current": current,
    }


def _continuity_snapshot(root: Path, task: Dict[str, str]) -> Dict[str, Any]:
    observation = _continuity_observation(root, task)
    if observation["cr_observation_state"] not in {"ready", "absent", "stale"}:
        return {"source_digest": None, "current": None}
    return {"source_digest": observation["cr_source_digest"], "current": observation["current"]}


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
    raw_path = _text(value.get("path"), "rollout.path")
    path = Path(raw_path).expanduser()
    if not path.is_absolute() or path.is_symlink():
        raise ContractError("rollout.path must be absolute")
    session_id = value.get("session_id")
    if session_id is not None:
        session_id = _text(session_id, "rollout.session_id")
    return {"path": str(path.resolve()), "session_id": session_id}


def resolve_rollout() -> Dict[str, str]:
    session_id = _text(os.environ.get("CODEX_THREAD_ID"), "CODEX_THREAD_ID")
    home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    if not home.is_absolute():
        raise ContractError("CODEX_HOME must be absolute")
    # shortcut: Codex state schema 5 only; review this adapter when Codex changes its metadata schema.
    database_path = _regular_file(home / "state_5.sqlite", "Codex metadata database")
    database = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
    try:
        rows = database.execute(
            "SELECT rollout_path FROM threads WHERE id = ?", (session_id,),
        ).fetchmany(2)
    finally:
        database.close()
    if len(rows) != 1:
        raise ContractError("Codex metadata must match exactly one current thread")
    path = Path(_text(rows[0][0], "Codex rollout path"))
    if not path.is_absolute():
        raise ContractError("Codex rollout path must be absolute")
    _regular_file(path, "Codex rollout")
    try:
        with path.open("r", encoding="utf-8") as handle:
            record = json.loads(handle.readline())
    except (ValueError, UnicodeError) as exc:
        raise ContractError("Codex rollout first record must be session metadata") from exc
    if (
        not isinstance(record, dict)
        or record.get("type") != "session_meta"
        or not isinstance(record.get("payload"), dict)
        or record["payload"].get("id") != session_id
    ):
        raise ContractError("Codex rollout session metadata does not match the current thread")
    rollout = {"path": str(path), "session_id": session_id}
    if contains_secret(rollout):
        raise ContractError("Codex rollout metadata contains a recognized secret")
    return rollout


def _short_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    return redact_text(compact)


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


@contextmanager
def _history_index():
    with tempfile.TemporaryDirectory(prefix="pennix-handoff-index-") as directory:
        database = sqlite3.connect(str(Path(directory) / "index.sqlite"))
        try:
            database.executescript("""
                PRAGMA cache_size=-2048;
                PRAGMA temp_store=FILE;
                PRAGMA journal_mode=OFF;
                CREATE TABLE topics(topic TEXT PRIMARY KEY, event INTEGER);
                CREATE TABLE repeats(topic TEXT, digest TEXT, n INTEGER, PRIMARY KEY(topic,digest));
                CREATE TABLE tools(id TEXT PRIMARY KEY, calls INTEGER DEFAULT 0, results INTEGER DEFAULT 0);
                CREATE TABLE counts(category TEXT, name TEXT, n INTEGER, PRIMARY KEY(category,name));
                CREATE TABLE candidates(id INTEGER PRIMARY KEY, kind TEXT, topic TEXT, digest TEXT, state TEXT, chars INTEGER, timeline INTEGER DEFAULT 0);
            """)
            yield database
        finally:
            database.close()


def _history_record(kind: str, value: Dict[str, Any]) -> str:
    return json.dumps({"type": kind, "value": value}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _topic_transition(database, topic: str, text_digest: str, event: int) -> tuple[int, Optional[int]]:
    row = database.execute("SELECT n FROM repeats WHERE topic=? AND digest=?", (topic, text_digest)).fetchone()
    repeat = 1 if row is None else row[0] + 1
    previous = database.execute("SELECT event FROM topics WHERE topic=?", (topic,)).fetchone()
    database.execute("INSERT OR REPLACE INTO repeats VALUES(?,?,?)", (topic, text_digest, repeat))
    database.execute("INSERT OR REPLACE INTO topics VALUES(?,?)", (topic, event))
    return repeat, None if previous is None else previous[0]


def _count(database, category: str, name: str) -> None:
    database.execute("INSERT INTO counts VALUES(?,?,1) ON CONFLICT(category,name) DO UPDATE SET n=n+1", (category, name))


def _tool_seen(database, kind: str, call_id: str) -> None:
    column = "calls" if kind == "tool_call" else "results"
    database.execute("INSERT OR IGNORE INTO tools(id) VALUES(?)", (call_id,))
    database.execute("UPDATE tools SET " + column + "=1 WHERE id=?", (call_id,))


def _rollout_descriptor(raw: Dict[str, Optional[str]], history_path: Path) -> tuple[Dict[str, Any], Dict[str, Any]]:
    path = _regular_file(Path(str(raw["path"])), "rollout source")
    session_id = raw["session_id"]
    counts = {kind: 0 for kind in HISTORY_TYPES}
    hasher = hashlib.sha256()
    history_bytes = history_chars = 0
    with _history_index() as database, history_path.open("xb") as output, path.open("rb") as handle:
        os.chmod(history_path, 0o600)
        def keep(kind: str, item: Dict[str, Any]) -> None:
            nonlocal history_bytes, history_chars
            encoded = _history_record(kind, item)
            data = encoded.encode("utf-8")
            output.write(data)
            hasher.update(data)
            history_bytes += len(data)
            history_chars += len(encoded)
            counts[kind] += 1

        start = os.fstat(handle.fileno())
        capture_size = start.st_size
        offset = line_number = record_count = event_index = 0
        while offset < capture_size:
            remaining = capture_size - offset
            raw_line = handle.readline(remaining + 1)
            if not raw_line:
                break
            if not raw_line.endswith(b"\n") and offset + len(raw_line) < capture_size:
                raise ContractError("rollout contains an incomplete record before capture boundary")
            if not raw_line.endswith(b"\n"):
                keep("omission", {"kind": "trailing_partial_record", "byte_start": offset, "bytes": len(raw_line)})
                break
            line_number += 1
            byte_start = offset
            offset += len(raw_line)
            if not raw_line.strip():
                continue
            if raw_line.rstrip(b"\r\n") and not raw_line.rstrip(b"\r\n").replace(b"\0", b""):
                keep("omission", {
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
            if record_count % 256 == 0:
                database.commit()
            record_type = _short_text(str(record.get("type", "unknown")))
            payload = record.get("payload")
            source = {"line": line_number, "byte_start": byte_start, "byte_end": offset, "record_type": record_type}
            if isinstance(record.get("timestamp"), str):
                source["timestamp"] = _short_text(record["timestamp"])
            payload_type = payload.get("type") if isinstance(payload, dict) else None
            if record_type == "compacted" or payload_type == "compacted":
                _count(database, "excluded", "compacted")
                keep("compacted_span", {
                    "line": line_number,
                    "byte_start": byte_start,
                    "byte_end": offset,
                    "bytes": len(raw_line),
                })
                continue
            role, message_text = _event_message(record_type, payload)
            if role and message_text:
                event_index += 1
                keep("candidate", {"kind": role, "event_index": event_index, "text": message_text, "source": source})
                if role == "user":
                    topic = _topic_key(message_text)
                    if topic:
                        repeat, previous = _topic_transition(database, topic, hashlib.sha256(message_text.encode()).hexdigest(), event_index)
                        item: Dict[str, Any] = {"topic_key": topic, "state": "repeated" if repeat > 1 else _timeline_state(message_text), "event_index": event_index, "repeat_count": repeat}
                        if previous is not None:
                            item["supersedes_event_index"] = previous
                        keep("timeline", item)
                continue
            if record_type != "response_item" or not isinstance(payload, dict):
                _count(database, "unknown", record_type)
                keep("unknown_span", {"record_type": _short_text(record_type), "line": line_number, "byte_start": byte_start, "byte_end": offset})
                continue
            item_type = str(payload.get("type", "unknown"))
            if item_type == "reasoning":
                _count(database, "excluded", "reasoning")
                continue
            if item_type == "message":
                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    _count(database, "excluded", _short_text("message:%s" % role))
                    continue
                _count(database, "excluded", "empty_public_message")
                continue
            if item_type in {"function_call", "custom_tool_call", "tool_call"}:
                call_id = _short_text(payload.get("call_id") or payload.get("id"))
                if call_id:
                    _tool_seen(database, "tool_call", call_id)
                event_index += 1
                item = {"kind": "tool_call", "event_index": event_index, "tool": _short_text(payload.get("name")), "source": source}
                if call_id:
                    item["call_id"] = call_id
                keep("candidate", item)
                continue
            if item_type in {"function_call_output", "custom_tool_call_output", "tool_result"}:
                call_id = _short_text(payload.get("call_id") or payload.get("id"))
                if call_id:
                    _tool_seen(database, "tool_result", call_id)
                event_index += 1
                item = {"kind": "tool_result", "event_index": event_index, "source": source}
                if call_id:
                    item["call_id"] = call_id
                keep("candidate", item)
                continue
            name = _short_text("response_item:%s" % item_type)
            _count(database, "unknown", name)
            keep("unknown_span", {"record_type": name, "line": line_number, "byte_start": byte_start, "byte_end": offset})
        capture_end = offset
        end = os.fstat(handle.fileno())
        if end.st_size < capture_end:
            raise ContractError("rollout source changed while being captured")
        for category, name, n in database.execute("SELECT category,name,n FROM counts ORDER BY category,name"):
            keep("count", {"category": category, "name": name, "count": n})
        for (call_id,) in database.execute("SELECT id FROM tools WHERE calls<>results ORDER BY id"):
            keep("incomplete_tool_call", {"call_id": call_id})
        output.flush()
        os.fsync(output.fileno())
    identity = {"path": str(path), "session_id": session_id, "capture_end": capture_end, "record_count": record_count, "parser_version": PARSER_VERSION}
    history = {
        "path": HISTORY_NAME, "sha256": hasher.hexdigest(), "bytes": history_bytes,
        "characters": history_chars, "records": sum(counts.values()), "counts": counts,
        "capture": {"source_bytes_at_capture": capture_size, "capture_end": capture_end, "record_count": record_count},
    }
    return identity, history


def _source(root: Path, task: Optional[Dict[str, str]], evidence: list[Dict[str, Any]], rollout: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task": task, "git": _git_snapshot(root), "evidence": evidence,
        "rollout_identity": {key: rollout[key] for key in ("path", "session_id", "capture_end", "record_count", "parser_version")},
    }


def _request(root: Path, path: Path) -> Dict[str, Any]:
    value = load_json_file(path)
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
    if not isinstance(memory_projection, dict) or set(memory_projection) - {"semantic_capsule", "local", "archive_refs"}:
        raise ContractError("memory_projection fields are invalid")
    normalized = {
        "session_label": _text(value["session_label"], "session_label"), "facts": _text_list(value["facts"], "facts"),
        "evidence_paths": evidence_paths, "next_action": _text(value["next_action"], "next_action"),
        "blockers": _text_list(value["blockers"], "blockers"), "risks": _text_list(value["risks"], "risks"),
        "validation": normalized_validation, "rollout": _read_rollout_path(value["rollout"]),
        "memory_projection": {
            "semantic_capsule": _text(memory_projection.get("semantic_capsule"), "memory_projection.semantic_capsule"),
            "local": _text_list(memory_projection.get("local", []), "memory_projection.local"),
            "archive_refs": _text_list(memory_projection.get("archive_refs", []), "memory_projection.archive_refs"),
        },
    }
    _evidence_snapshot(root, evidence_paths)
    if contains_secret(normalized):
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


def build(root: Path, request: Dict[str, Any], handoff_id: str, history_path: Path) -> Dict[str, Any]:
    rollout, history = _rollout_descriptor(request["rollout"], history_path)
    evidence = _evidence_snapshot(root, request["evidence_paths"])
    task = _task_snapshot(root)
    source = _source(root, task, evidence, rollout)
    payload: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "kind": KIND, "handoff_id": handoff_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "project": {"name": root.name},
        "work_context": {"task": task},
        "source": {"session_label": request["session_label"], "git": source["git"], "evidence": evidence, "rollout": source["rollout_identity"]},
        "verified": {"facts": request["facts"], "validation": request["validation"]},
        "history": history,
        "pending": {"next_action": request["next_action"], "blockers": request["blockers"], "risks": request["risks"]},
        "memory_projection": request["memory_projection"], "authorization": dict(AUTHORIZATION),
    }
    return payload


def _source_position(value: Dict[str, Any], boundary: int, label: str) -> None:
    _integer(value.get("line"), label + ".line", 1)
    start = _integer(value.get("byte_start"), label + ".byte_start")
    end = _integer(value.get("byte_end"), label + ".byte_end", start + 1)
    if end > boundary:
        raise ContractError(label + " exceeds capture boundary")


def _history_path(root: Path, payload: Dict[str, Any]) -> Path:
    return _destination(root, create_id=payload["handoff_id"])[1].with_name(HISTORY_NAME)


def _validate_history(path: Path, history: Dict[str, Any], rollout: Dict[str, Any]) -> None:
    _fields(history, {"path", "sha256", "bytes", "characters", "records", "counts", "capture"}, "history")
    if history["path"] != HISTORY_NAME or not isinstance(history["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", history["sha256"]):
        raise ContractError("history path or digest is invalid")
    _fields(history["counts"], HISTORY_TYPES, "history counts")
    for name in ("bytes", "characters", "records"):
        _integer(history[name], "history." + name)
    for name in HISTORY_TYPES:
        _integer(history["counts"][name], "history count")
    capture = _fields(history["capture"], {"source_bytes_at_capture", "capture_end", "record_count"}, "history capture")
    for name in capture:
        _integer(capture[name], "history capture." + name)
    boundary, size, source_records = capture["capture_end"], capture["source_bytes_at_capture"], capture["record_count"]
    if boundary > size or boundary != rollout["capture_end"] or source_records != rollout["record_count"]:
        raise ContractError("history capture and rollout disagree")
    _regular_file(path, "history")
    digest, byte_count, char_count = hashlib.sha256(), 0, 0
    counts = {kind: 0 for kind in HISTORY_TYPES}
    previous_end = previous_line = previous_timeline = trailing = excluded = compacted_reported = 0
    previous_count = previous_incomplete = None
    phase = 0
    with _history_index() as database, path.open("rb") as handle:
        for raw in handle:
            try:
                text = raw.decode("utf-8")
                record = json.loads(text)
            except (UnicodeError, ValueError, RecursionError) as exc:
                raise ContractError("history JSONL record is invalid") from exc
            _fields(record, {"type", "value"}, "history record")
            kind, item = record["type"], record["value"]
            if not isinstance(kind, str) or kind not in HISTORY_TYPES or not isinstance(item, dict):
                raise ContractError("history record type/value is invalid")
            if text != _history_record(kind, item) or contains_secret(record):
                raise ContractError("history record is noncanonical or unsafe")
            digest.update(raw)
            byte_count += len(raw)
            char_count += len(text)
            counts[kind] += 1
            if kind not in {"count", "incomplete_tool_call"} and phase:
                raise ContractError("history source records are out of order")
            if kind not in {"count", "incomplete_tool_call"} and trailing:
                raise ContractError("history source records follow the partial capture tail")
            source = None
            if kind == "candidate":
                event = _integer(item.get("event_index"), "candidate.event_index", 1)
                if event != counts[kind]:
                    raise ContractError("candidate event indices must be consecutive")
                role = _text(item.get("kind"), "candidate.kind")
                fields = {"kind", "event_index", "source"}
                topic = text_digest = state = None
                if role in {"user", "assistant"}:
                    fields.add("text")
                    message = _text(item.get("text"), "candidate.text")
                    text_digest = hashlib.sha256(message.encode()).hexdigest()
                    if role == "user":
                        topic, state = _topic_key(message), _timeline_state(message)
                elif role in {"tool_call", "tool_result"}:
                    if role == "tool_call":
                        fields.add("tool")
                        if item.get("tool") is not None:
                            _text(item["tool"], "candidate.tool")
                    if "call_id" in item:
                        fields.add("call_id")
                        _tool_seen(database, role, _text(item["call_id"], "candidate.call_id"))
                else:
                    raise ContractError("candidate kind is invalid")
                _fields(item, fields, "candidate")
                source = item["source"]
                source_fields = {"line", "byte_start", "byte_end", "record_type"}
                if isinstance(source, dict) and "timestamp" in source:
                    source_fields.add("timestamp")
                    _text(source["timestamp"], "candidate timestamp")
                _fields(source, source_fields, "candidate source")
                _text(source["record_type"], "candidate record_type")
                database.execute("INSERT INTO candidates(id,kind,topic,digest,state,chars) VALUES(?,?,?,?,?,?)", (event, role, topic, text_digest, state, len(_json_view(item))))
            elif kind == "timeline":
                fields = {"topic_key", "state", "event_index", "repeat_count"}
                if "supersedes_event_index" in item:
                    fields.add("supersedes_event_index")
                    _integer(item["supersedes_event_index"], "timeline supersedes", 1)
                _fields(item, fields, "timeline")
                event = _integer(item["event_index"], "timeline.event_index", previous_timeline + 1)
                candidate = database.execute("SELECT kind,topic,digest,state FROM candidates WHERE id=?", (event,)).fetchone()
                if candidate is None or candidate[0] != "user" or item["topic_key"] != candidate[1] or candidate[1] is None:
                    raise ContractError("timeline candidate/topic reference is invalid")
                repeat, previous = _topic_transition(database, candidate[1], candidate[2], event)
                if _integer(item["repeat_count"], "timeline.repeat_count", 1) != repeat or item["state"] != ("repeated" if repeat > 1 else candidate[3]) or item.get("supersedes_event_index") != previous:
                    raise ContractError("timeline repeat/state/supersedes reference is inconsistent")
                database.execute("UPDATE candidates SET timeline=1 WHERE id=?", (event,))
                previous_timeline = event
            elif kind in {"omission", "unknown_span", "compacted_span"}:
                if kind == "omission" and item.get("kind") == "trailing_partial_record":
                    _fields(item, {"kind", "byte_start", "bytes"}, "partial record")
                    if _integer(item["byte_start"], "partial start") != boundary or boundary + _integer(item["bytes"], "partial bytes", 1) != size:
                        raise ContractError("trailing partial capture is inconsistent")
                    trailing += 1
                else:
                    fields = {"line", "byte_start", "byte_end"}
                    if kind == "unknown_span":
                        fields.add("record_type")
                        _count(database, "observed", _text(item.get("record_type"), "unknown record_type"))
                    else:
                        fields.add("bytes")
                        if kind == "omission":
                            fields.add("kind")
                            if item.get("kind") != "nul_padding_record":
                                raise ContractError("history omission is invalid")
                    _fields(item, fields, "history span")
                    _source_position(item, boundary, "history span")
                    if "bytes" in item and _integer(item["bytes"], "span bytes", 1) != item["byte_end"] - item["byte_start"]:
                        raise ContractError("history span length is inconsistent")
                    source = item
            elif kind == "count":
                if phase == 2:
                    raise ContractError("history counts are out of order")
                phase = 1
                _fields(item, {"category", "name", "count"}, "history count")
                category = _text(item["category"], "count category")
                name = _text(item["name"], "count name")
                if category not in {"excluded", "unknown"} or (previous_count is not None and (category, name) <= previous_count):
                    raise ContractError("history count category/order is invalid")
                n = _integer(item["count"], "count", 1)
                if category == "unknown":
                    row = database.execute("SELECT n FROM counts WHERE category='observed' AND name=?", (name,)).fetchone()
                    if row is None or row[0] != n:
                        raise ContractError("unknown spans and counts disagree")
                    database.execute("DELETE FROM counts WHERE category='observed' AND name=?", (name,))
                else:
                    excluded += n
                    if name == "compacted":
                        compacted_reported = n
                previous_count = (category, name)
            else:
                phase = 2
                _fields(item, {"call_id"}, "incomplete tool")
                call_id = _text(item["call_id"], "incomplete tool id")
                row = database.execute("SELECT id FROM tools WHERE calls<>results AND (? IS NULL OR id>?) ORDER BY id LIMIT 1", (previous_incomplete, previous_incomplete)).fetchone()
                if row is None or row[0] != call_id:
                    raise ContractError("incomplete tool references disagree")
                previous_incomplete = call_id
            if source is not None:
                _source_position(source, boundary, "history source")
                if source["byte_start"] < previous_end or source["line"] <= previous_line:
                    raise ContractError("history source positions are out of order")
                previous_end, previous_line = source["byte_end"], source["line"]
            if sum(counts.values()) % 256 == 0:
                database.commit()
        if database.execute("SELECT 1 FROM counts WHERE category='observed' LIMIT 1").fetchone() or database.execute("SELECT 1 FROM candidates WHERE topic IS NOT NULL AND timeline=0 LIMIT 1").fetchone():
            raise ContractError("history references or coverage counts are incomplete")
        if database.execute("SELECT count(*) FROM tools WHERE calls<>results").fetchone()[0] != counts["incomplete_tool_call"]:
            raise ContractError("history incomplete tool count disagrees")
    if (boundary < size) != (trailing == 1) or trailing > 1:
        raise ContractError("trailing partial coverage is inconsistent")
    if counts["candidate"] + counts["unknown_span"] + excluded != source_records:
        raise ContractError("history coverage disagrees with source record count")
    if compacted_reported != counts["compacted_span"]:
        raise ContractError("compacted spans and counts disagree")
    if history["counts"] != counts or history["records"] != sum(counts.values()) or history["bytes"] != byte_count or history["characters"] != char_count or history["sha256"] != digest.hexdigest():
        raise ContractError("history binding is invalid")


def _validate_payload_shape(root: Path, payload: Dict[str, Any], handoff_id: str, history_path: Optional[Path] = None) -> None:
    if not isinstance(payload, dict):
        raise ContractError("handoff core must be an object")
    expected = {"schema_version", "kind", "handoff_id", "created_at", "project", "work_context", "source", "verified", "history", "pending", "memory_projection", "authorization"}
    if set(payload) != expected or type(payload["schema_version"]) is not int or payload["schema_version"] != SCHEMA_VERSION or payload["kind"] != KIND:
        raise ContractError("handoff schema is unsupported")
    if payload["handoff_id"] != handoff_id or not HANDOFF_ID.fullmatch(handoff_id):
        raise ContractError("handoff id does not match package path")
    _text(payload["created_at"], "created_at")
    if _fields(payload["project"], {"name"}, "handoff project")["name"] != root.name:
        raise ContractError("handoff project identity is invalid")
    context = payload["work_context"]
    if not isinstance(context, dict) or set(context) != {"task"}:
        raise ContractError("handoff work context is invalid")
    task = context["task"]
    if task is not None:
        _fields(task, {"id", "path", "status", "continuity"}, "handoff task")
        for key in ("id", "path", "status"):
            _text(task[key], "task." + key)
        if not task["path"].startswith(".trellis/tasks/"):
            raise ContractError("handoff task path is unsafe")
        _project_file(root, task["path"], "task path")
        continuity = _fields(task["continuity"], {"source_digest", "current"}, "task continuity")
        digest, current = continuity["source_digest"], continuity["current"]
        if digest is None and current is None:
            pass
        elif (
            not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not isinstance(current, dict)
            or current.get("task") != {"id": task["id"], "path": task["path"], "status": task["status"]}
        ):
            raise ContractError("task continuity projection does not match task snapshot")
    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"session_label", "git", "evidence", "rollout"}:
        raise ContractError("handoff source is invalid")
    _text(source["session_label"], "source.session_label")
    git = _fields(source["git"], {"branch", "head", "worktree_state", "recent_commits"}, "source.git")
    for key in ("branch", "head"):
        if git[key] is not None:
            _text(git[key], "git." + key)
    if _text(git["worktree_state"], "git.worktree_state") not in {"dirty", "clean"}:
        raise ContractError("git worktree state is invalid")
    _text_list(git["recent_commits"], "git.recent_commits")
    if not isinstance(source["evidence"], list):
        raise ContractError("handoff evidence is invalid")
    for item in source["evidence"]:
        _fields(item, {"path"}, "handoff evidence item")
        _project_file(root, _text(item["path"], "evidence.path"), "evidence path")
    rollout = source["rollout"]
    rollout_expected = {"path", "session_id", "capture_end", "record_count", "parser_version"}
    if not isinstance(rollout, dict) or set(rollout) != rollout_expected:
        raise ContractError("handoff rollout descriptor is invalid")
    if not Path(_text(rollout["path"], "rollout.path")).is_absolute():
        raise ContractError("rollout path must be absolute")
    if rollout["session_id"] is not None:
        _text(rollout["session_id"], "rollout.session_id")
    for field in ("capture_end", "record_count"):
        _integer(rollout[field], "rollout." + field)
    if rollout["parser_version"] != PARSER_VERSION:
        raise ContractError("rollout parser version is unsupported")
    _validate_history(history_path or _history_path(root, payload), payload["history"], rollout)
    verified = payload["verified"]
    if not isinstance(verified, dict) or set(verified) != {"facts", "validation"}:
        raise ContractError("handoff verified context is invalid")
    _text_list(verified["facts"], "verified.facts")
    if not isinstance(verified["validation"], list):
        raise ContractError("handoff validation is invalid")
    for item in verified["validation"]:
        _fields(item, {"command", "result"}, "verified.validation item")
        _text(item["command"], "validation.command")
        _text(item["result"], "validation.result")
    pending = payload["pending"]
    if not isinstance(pending, dict) or set(pending) != {"next_action", "blockers", "risks"}:
        raise ContractError("handoff pending context is invalid")
    _text(pending["next_action"], "pending.next_action")
    _text_list(pending["blockers"], "pending.blockers")
    _text_list(pending["risks"], "pending.risks")
    memory = payload["memory_projection"]
    if not isinstance(memory, dict):
        raise ContractError("handoff memory projection is invalid")
    fields = {"semantic_capsule", "local", "archive_refs"}
    if set(memory) != fields:
        raise ContractError("handoff memory projection is invalid")
    _text(memory["semantic_capsule"], "memory_projection.semantic_capsule")
    for field in fields - {"semantic_capsule"}:
        _text_list(memory[field], "memory_projection.%s" % field)
    if payload["authorization"] != AUTHORIZATION:
        raise ContractError("handoff authorization is invalid")
    if contains_secret(payload):
        raise ContractError("handoff core contains a possible credential or secret")


def validate(root: Path, payload: Dict[str, Any], handoff_id: str, history_path: Optional[Path] = None) -> str:
    _validate_payload_shape(root, payload, handoff_id, history_path)
    return "ready"


def _json_view(value: Dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _candidate_view(path: Path, event_index: int) -> str:
    _integer(event_index, "event_index", 1)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["type"] == "candidate" and record["value"]["event_index"] == event_index:
                return _json_view(record["value"])
    raise ContractError("history event_index is unavailable")


def _history_page(path: Path, offset: int, length: int) -> str:
    position, remaining, pieces = 0, length, []
    with path.open("r", encoding="utf-8", newline="") as handle:
        while remaining:
            text = handle.read(65536)
            if not text:
                break
            end = position + len(text)
            if end > offset:
                piece = text[max(0, offset - position):max(0, offset - position) + remaining]
                pieces.append(piece)
                remaining -= len(piece)
            position = end
    return "".join(pieces)


def _text_page(path: Path, offset: int, length: int) -> tuple[str, int]:
    _regular_file(path, "handoff text view")
    total, parts = 0, []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), ""):
            if total + len(chunk) > offset and total < offset + length:
                parts.append(chunk[max(0, offset - total):max(0, offset + length - total)])
            total += len(chunk)
    if offset > total:
        raise ContractError("read offset exceeds view length")
    return "".join(parts), total


def read_view(root: Path, handoff_path: str, view: str, offset: int, length: int, event_index: Optional[int] = None) -> Dict[str, Any]:
    handoff_id, _ = _destination(root, handoff_path=handoff_path)
    with storage.open_package(root, handoff_id) as (directory, kind):
        return _read_package_view(root, handoff_id, directory, kind, view, offset, length, event_index)


def _read_package_view(root: Path, handoff_id: str, directory: Path, kind: str, view: str, offset: int, length: int, event_index: Optional[int]) -> Dict[str, Any]:
    _integer(offset, "read offset")
    _integer(length, "read length", 1)
    core = directory / HANDOFF_NAME
    identity = storage.historical_identity(core)
    version = identity.get("schema_version")
    if identity.get("handoff_id") != handoff_id or identity.get("kind") != KIND or not isinstance(identity.get("project"), dict) or identity["project"].get("name") != root.name:
        raise ContractError("historical package identity differs")
    historical = version != SCHEMA_VERSION
    if historical:
        if version not in {4, 6, 8, 9, 11}:
            raise ContractError("historical schema is unknown; inspect original asset without admission")
        if event_index is not None or view not in {"core", "history", "prompt"}:
            raise ContractError("historical original view has no candidate index")
        file = directory / "session-handoff-prompt.md" if view == "prompt" else core if view == "core" or not (directory / HISTORY_NAME).exists() else directory / HISTORY_NAME
        text, total = _text_page(file, offset, length)
        return {"handoff_id": handoff_id, "view": view, "event_index": None, "offset": offset, "next_offset": min(offset + length, total), "total_chars": total, "complete": offset + length >= total, "text": text, "storage_kind": kind, "schema_version": version, "qualification": "historical_original_readonly", "admission_eligible": False}
    payload = load_json_file(core)
    validate(root, payload, handoff_id, core.with_name(HISTORY_NAME))
    if view == "prompt" and event_index is None:
        text, total = _text_page(directory / "session-handoff-prompt.md", offset, length)
        if contains_secret(text):
            raise ContractError("paired handoff prompt contains a possible credential")
        return {"handoff_id": handoff_id, "view": view, "event_index": None, "offset": offset, "next_offset": min(offset + length, total), "total_chars": total, "complete": offset + length >= total, "text": text, "storage_kind": kind}
    content = None
    if view == "core" and event_index is None:
        content = _json_view(payload)
    elif view == "history":
        if event_index is not None:
            content = _candidate_view(core.with_name(HISTORY_NAME), event_index)
    else:
        raise ContractError("read view or event_index is invalid")
    total = len(content) if content is not None else payload["history"]["characters"]
    if offset > total:
        raise ContractError("read offset exceeds view length")
    end = min(offset + length, total)
    text = content[offset:end] if content is not None else _history_page(core.with_name(HISTORY_NAME), offset, length)
    return {"handoff_id": handoff_id, "view": view, "event_index": event_index, "offset": offset, "next_offset": end, "total_chars": total, "complete": end == total, "text": text, "storage_kind": kind}


def _validate_history_reading(root: Path, payload: Dict[str, Any], attestation: Dict[str, Any]) -> None:
    lengths: dict[Optional[int], int] = {None: payload["history"]["characters"]}
    full_ranges: list[tuple[int, int]] = []
    for reference in attestation["history_refs"]:
        event_index = reference["event_index"]
        if event_index not in lengths:
            lengths[event_index] = len(_candidate_view(_history_path(root, payload), event_index))
        if reference["next_offset"] > lengths[event_index]:
            raise ContractError("history reading range exceeds view length")
        if event_index is None:
            full_ranges.append((reference["offset"], reference["next_offset"]))
    if attestation["history_read"] == "full":
        end = 0
        for start, stop in sorted(full_ranges):
            if start > end:
                raise ContractError("full history reading contains a gap")
            end = max(end, stop)
        if end != lengths.get(None):
            raise ContractError("full history reading requires the entire history view")


def _atomic_json(destination: Path, payload: Dict[str, Any], history_path: Path) -> None:
    base = destination.parent.parent
    if base.is_symlink():
        raise ContractError("session-handoffs directory is unsafe")
    base.mkdir(parents=True, exist_ok=True)
    os.chmod(base, 0o700)
    temporary = Path(tempfile.mkdtemp(prefix="." + payload["handoff_id"] + ".", dir=base))
    lock = base / ("." + payload["handoff_id"] + ".publish-lock")
    lock_fd = None
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        history = temporary / HISTORY_NAME
        shutil.copyfile(history_path, history)
        os.chmod(history, 0o600)
        with history.open("rb") as handle:
            os.fsync(handle.fileno())
        _validate_history(history, payload["history"], payload["source"]["rollout"])
        with (temporary / HANDOFF_NAME).open("w", encoding="utf-8") as handle:
            handle.write(_json_view(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary / HANDOFF_NAME, 0o600)
        if destination.parent.exists():
            raise ContractError("handoff package already exists")
        os.rename(temporary, destination.parent)
        directory_fd = os.open(base, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            lock.unlink()


def _lifecycle_path(root: Path, handoff_id: str) -> Path:
    safe_id(handoff_id, "handoff_id")
    runtime = root / ".trellis" / ".runtime"
    base = root / LIFECYCLE_RUNTIME
    for path in (runtime, base):
        if path.is_symlink():
            raise ContractError("handoff lifecycle directory is unsafe")
    legacy = base / (handoff_id + ".jsonl")
    canonical = storage.package_directory(root, handoff_id) / storage.LIFECYCLE
    if canonical.exists():
        if legacy.exists() and not _receipt_prefix(legacy, canonical):
            raise ContractError("handoff lifecycle copies diverge; inspect exact package")
        return canonical
    return legacy if legacy.exists() else canonical


def _receipt_prefix(prefix: Path, full: Path) -> bool:
    _regular_file(prefix, "lifecycle prefix")
    _regular_file(full, "lifecycle copy")
    with prefix.open("rb") as left, full.open("rb") as right:
        for chunk in iter(lambda: left.read(storage.CHUNK), b""):
            if right.read(len(chunk)) != chunk:
                return False
    return True


def _archive_path(root: Path, handoff_id: str) -> Path:
    safe_id(handoff_id, "handoff_id")
    runtime = root / ".trellis" / ".runtime"
    base = root / ARCHIVE_RUNTIME
    for path in (runtime, base):
        if path.is_symlink():
            raise ContractError("handoff archive directory is unsafe")
    return base / handoff_id


def _require_current(payload: Dict[str, Any]) -> None:
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ContractError("handoff schema is unsupported; create a current package")


def _core(root: Path, handoff_path: str, *, mutable: bool = False) -> tuple[str, Path, Dict[str, Any]]:
    handoff_id, destination = _destination(root, handoff_path=handoff_path)
    _regular_file(destination, "handoff path")
    payload = load_json_file(destination)
    if validate(root, payload, handoff_id) != "ready":
        raise ContractError("handoff core is not ready")
    if mutable:
        _require_current(payload)
        if storage.zip_path(root, handoff_id).exists():
            raise ContractError("archived handoff cannot change admission or task ownership; use a new handoff")
    return handoff_id, destination, payload


def _read_paired_prompt(root: Path, handoff_path: str) -> None:
    _, core = _destination(root, handoff_path=handoff_path)
    _read_paired_prompt_directory(core.parent)


def _read_paired_prompt_directory(directory: Path) -> None:
    prompt = _regular_file(directory / "session-handoff-prompt.md", "paired handoff prompt")
    try:
        if contains_secret(prompt.read_text(encoding="utf-8")):
            raise ContractError("paired handoff prompt contains a possible credential")
    except (OSError, UnicodeError) as exc:
        raise ContractError("paired handoff prompt is unreadable") from exc


def _event_shape(event: Any, handoff_id: str) -> Dict[str, Any]:
    if not isinstance(event, dict):
        raise ContractError("lifecycle event schema is invalid")
    base_fields = {
        "schema_version", "kind", "handoff_id", "event_type", "source_status", "target_status",
        "retention_status", "observed_at", "actor", "evidence_refs",
    }
    cr_fields = {"cr_status", "cr_source_digest", "cr_observed_at", "cr_observation_state"}
    schema_version = event.get("schema_version")
    event_type = event.get("event_type")
    expected = base_fields | (cr_fields if schema_version == LIFECYCLE_SCHEMA_VERSION and event_type == "prepare" else set())
    if set(event) != expected or type(schema_version) is not int or schema_version not in {2, LIFECYCLE_SCHEMA_VERSION}:
        raise ContractError("lifecycle event schema is invalid")
    if schema_version == 2 and set(event) != base_fields:
        raise ContractError("legacy lifecycle event schema is invalid")
    if event["kind"] != LIFECYCLE_EVENT_KIND or event["handoff_id"] != handoff_id:
        raise ContractError("lifecycle event identity is invalid")
    _text(event_type, "event.event_type")
    for field, values in (("source_status", SOURCE_STATES), ("target_status", TARGET_STATES), ("retention_status", RETENTION_STATES)):
        value = _text(event[field], "event.%s" % field)
        if value not in values:
            raise ContractError("event.%s is invalid" % field)
    _text(event["observed_at"], "event.observed_at")
    if event["actor"] != LIFECYCLE_ACTOR:
        raise ContractError("event.actor is invalid")
    _text_list(event["evidence_refs"], "event.evidence_refs")
    if schema_version == LIFECYCLE_SCHEMA_VERSION and event_type == "prepare":
        cr_status = event["cr_status"]
        cr_digest = event["cr_source_digest"]
        cr_state = event["cr_observation_state"]
        if cr_status is not None and (not isinstance(cr_status, str) or cr_status not in {"ready", "absent", "stale", "withheld"}):
            raise ContractError("event.cr_status is invalid")
        if cr_digest is not None and (not isinstance(cr_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", cr_digest)):
            raise ContractError("event.cr_source_digest is invalid")
        _text(event["cr_observed_at"], "event.cr_observed_at")
        if not isinstance(cr_state, str) or cr_state not in CR_OBSERVATION_STATES:
            raise ContractError("event.cr_observation_state is invalid")
        if cr_state in {"ready", "stale"} and (cr_status != cr_state or cr_digest is None):
            raise ContractError("event CR observation is incomplete")
        if cr_state == "absent" and cr_status != "absent":
            raise ContractError("event CR absence is inconsistent")
        if cr_state == "withheld" and cr_status not in {"ready", "absent", "stale", "withheld", None}:
            raise ContractError("event CR withholding is inconsistent")
        if cr_state == "unavailable" and (cr_status is not None or cr_digest is not None):
            raise ContractError("unavailable CR observation must not report a CR result")
    if contains_secret(event):
        raise ContractError("lifecycle event contains a possible credential or secret")
    return event


def _transition(axis: str, old: str, new: str) -> bool:
    if old == new:
        return True
    transitions = {
        "source": {
            "unprepared": {"prepared", "failed"},
            "prepared": {"boundary_sealed", "pending", "unsupported", "unavailable", "failed"},
            "boundary_sealed": {"failed"},
            "pending": {"boundary_sealed", "unsupported", "unavailable", "failed"},
            "unsupported": {"boundary_sealed", "pending", "failed"},
            "unavailable": {"boundary_sealed", "pending", "failed"},
            "failed": {"failed"}, "expired": set(),
        },
        "target": {"not_admitted": {"admitted", "reconciled", "blocked"}, "admitted": {"reconciled", "blocked", "disposed"}, "reconciled": {"disposed"}, "blocked": {"admitted", "reconciled", "disposed"}, "disposed": set()},
        "retention": {"none": {"archive_eligible"}, "archive_eligible": {"archived"}, "archived": {"retained", "restored", "reopened", "purged"}, "retained": {"restored", "reopened", "purged"}, "restored": {"reopened", "purged"}, "reopened": {"purged"}, "purged": {"restored"}},
    }
    return new in transitions[axis].get(old, set())


class _ReceiptEvents:
    """Repeatable disk scan; retain only the count and last receipt."""

    def __init__(self, path: Path, handoff_id: str):
        self.path, self.handoff_id = path, handoff_id
        self.count, self.last = 0, None
        for event in self:
            self.count += 1
            self.last = event

    def __iter__(self):
        if not self.path.exists():
            return
        _regular_file(self.path, "lifecycle receipt")
        states = {"source": "unprepared", "target": "not_admitted", "retention": "none"}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                for raw in handle:
                    if not raw.endswith("\n"):
                        raise ContractError("lifecycle receipt contains an incomplete line")
                    try:
                        event = _event_shape(json.loads(raw), self.handoff_id)
                    except (ValueError, RecursionError) as exc:
                        if isinstance(exc, ContractError):
                            raise
                        raise ContractError("lifecycle receipt contains invalid JSON") from exc
                    for axis, key in (("source", "source_status"), ("target", "target_status"), ("retention", "retention_status")):
                        if not _transition(axis, states[axis], event[key]):
                            raise ContractError("lifecycle %s transition is invalid" % axis)
                    states = {"source": event["source_status"], "target": event["target_status"], "retention": event["retention_status"]}
                    yield event
        except (OSError, UnicodeError) as exc:
            raise ContractError("lifecycle receipt is unreadable") from exc

    def __len__(self):
        return self.count

    def __getitem__(self, index):
        if index != -1 or self.last is None:
            raise IndexError(index)
        return self.last


def _read_events(path: Path, handoff_id: str) -> _ReceiptEvents:
    return _ReceiptEvents(path, handoff_id)


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
    return _text(mode, "recorded lifecycle mode")


def _reconciled_admit_target(events: list[Dict[str, Any]]) -> Optional[str]:
    target = None
    for event in events:
        if event["event_type"] != "admit" or event["target_status"] != "reconciled":
            continue
        if target is not None:
            raise ContractError("handoff asset has multiple successful consumers")
        target = _admission_target(event)
    return target


def _admission_target(event: Dict[str, Any]) -> str:
    refs = [reference.removeprefix("target=") for reference in event["evidence_refs"] if reference.startswith("target=")]
    if len(refs) != 1:
        raise ContractError("admission target is invalid")
    target = refs[0]
    if not TARGET_SOURCE_RE.fullmatch(target):
        raise ContractError("admission target is invalid")
    return target


def _admission_steps(event: Dict[str, Any]) -> tuple[str, ...]:
    refs = [reference.removeprefix("steps=") for reference in event["evidence_refs"] if reference.startswith("steps=")]
    if not refs and event["target_status"] == "reconciled":
        return CONSUMPTION_STEPS
    if len(refs) != 1:
        raise ContractError("admission progress is invalid")
    steps = tuple(filter(None, refs[0].split(",")))
    if steps != CONSUMPTION_STEPS[:len(steps)]:
        raise ContractError("admission progress is invalid")
    return steps


def _consumption_attempt_target(events: list[Dict[str, Any]]) -> Optional[str]:
    # Legacy partial admissions remain readable, but only a complete
    # reconciliation consumes a handoff asset.
    return _reconciled_admit_target(events)


def _consumption_attempt_steps(events: list[Dict[str, Any]], target: str) -> tuple[str, ...]:
    completed: tuple[str, ...] = ()
    for event in events:
        if event["event_type"] != "admit" or event["target_status"] != "reconciled":
            continue
        if _admission_target(event) != target:
            continue
        steps = _admission_steps(event)
        if len(steps) < len(completed) or steps[:len(completed)] != completed:
            raise ContractError("admission progress regressed")
        completed = steps
    return completed


def _attestation_steps(attestation: Dict[str, Any]) -> tuple[str, ...]:
    steps: list[str] = []
    incomplete = False
    for step in CONSUMPTION_STEPS:
        if attestation[step]:
            if incomplete:
                raise ContractError("attestation consumption steps are out of order")
            steps.append(step)
        else:
            incomplete = True
    return tuple(steps)


def _source_ready(mode: str, state: dict[str, str]) -> bool:
    return mode == "core_only" and state["source"] == "boundary_sealed"


def _source_task_ready(payload: Dict[str, Any], events: list[Dict[str, Any]]) -> bool:
    if payload["work_context"]["task"] is None:
        return True
    receipts = {
        event["event_type"]: event["evidence_refs"]
        for event in events
        if event["event_type"] in {"ownership_quiesce", "ownership_seal"}
    }
    return (
        "ownership_status=quiescing" in receipts.get("ownership_quiesce", [])
        and "ownership_status=sealed" in receipts.get("ownership_seal", [])
    )


def _read_ownership_intent(path: Path, handoff_id: str) -> Optional[dict]:
    if not path.exists():
        return None
    _regular_file(path, "ownership operation intent")
    if path.stat().st_size > 64 * 1024:
        raise ContractError("ownership operation intent exceeds budget")
    value = load_json_file(path)
    required = {"schema_version", "kind", "handoff_id", "operation", "session", "package_digest", "expected_generation", "expected_continuity_digest", "native_before_digest", "receipt_fingerprint"}
    if set(value) != required or type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["kind"] != "pennix-handoff-ownership-intent" or value["handoff_id"] != handoff_id:
        raise ContractError("ownership operation intent identity is invalid")
    if value["operation"] not in {"quiesce", "seal", "retire", "claim", "consume", "release"}:
        raise ContractError("ownership operation intent action is invalid")
    safe_id(value["session"], "ownership operation session")
    _integer(value["expected_generation"], "ownership intent generation")
    for key in ("package_digest", "native_before_digest", "expected_continuity_digest"):
        if key == "expected_continuity_digest" and value[key] is None:
            continue
        if not isinstance(value[key], str) or not re.fullmatch(r"[a-f0-9]{64}", value[key]):
            raise ContractError("ownership operation intent digest is invalid")
    record = value["receipt_fingerprint"]
    if not isinstance(record, list) or len(record) != 5 or not all(type(part) is int for part in record):
        raise ContractError("ownership operation receipt identity is invalid")
    return value


def _append_event(
    root: Path, handoff_id: str, event_type: str, desired: dict[str, str], evidence_refs: list[str],
    *, cr_observation: Optional[Dict[str, Any]] = None, operation_intent: Optional[dict] = None,
) -> dict[str, Any]:
    with storage.lock(root):
        _regular_file(storage.package_directory(root, handoff_id) / HANDOFF_NAME, "lifecycle package")
        if storage.zip_path(root, handoff_id).exists():
            raise ContractError("handoff is archived; retention does not restore admission authority")
        intent_path = storage.package_directory(root, handoff_id) / storage.OWNERSHIP_INTENT
        observed = _read_ownership_intent(intent_path, handoff_id)
        if observed != operation_intent:
            raise ContractError("handoff ownership operation is pending or its identity changed")
        return _append_event_locked(root, handoff_id, event_type, desired, evidence_refs, cr_observation=cr_observation)


def _append_event_locked(
    root: Path, handoff_id: str, event_type: str, desired: dict[str, str], evidence_refs: list[str],
    *, cr_observation: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    path = _lifecycle_path(root, handoff_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    with path.open("a+", encoding="utf-8") as handle:
        handle.seek(0)
        events = _read_events(path, handoff_id)
        current = _state(events)
        if event_type == "prepare":
            if cr_observation is None:
                raise ContractError("prepare requires a Continuity Record observation")
            existing = next((event for event in events if event["event_type"] == "prepare"), None)
            if existing is not None:
                if _prepared_mode(events) != next((ref.removeprefix("mode=") for ref in evidence_refs if ref.startswith("mode=")), None):
                    raise ContractError("handoff lifecycle mode is immutable")
                if existing["evidence_refs"] != evidence_refs:
                    raise ContractError("handoff prepared source identity is immutable")
                return {"status": "idempotent", "state": current}
        if event_type == "admit":
            admission = {"evidence_refs": evidence_refs, "target_status": desired["target"]}
            target = _admission_target(admission)
            attempt_target = _consumption_attempt_target(events)
            if attempt_target is not None and attempt_target != target:
                raise ContractError("handoff asset has already been consumed by another target")
            if current["target"] == "reconciled" and attempt_target == target:
                return {"status": "idempotent", "state": current, "target": target}
            if desired["target"] in {"admitted", "reconciled"}:
                steps = _admission_steps(admission)
                completed = _consumption_attempt_steps(events, target)
                if len(steps) < len(completed) or steps[:len(completed)] != completed:
                    raise ContractError("admission progress regressed")
        if current == desired and any(old["event_type"] == event_type and old["evidence_refs"] == evidence_refs for old in events):
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
        if event_type == "prepare":
            event.update({key: cr_observation[key] for key in ("cr_status", "cr_source_digest", "cr_observed_at", "cr_observation_state")})
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
    if not isinstance(value, dict) or "current_task" not in value:
        raise ContractError("task.py current returned invalid JSON")
    if value.get("error") or value.get("stale") or value.get("source") == "unbound_ambiguous":
        raise ContractError("task.py current is stale, ambiguous, or unreadable")
    if value["current_task"] is None and value.get("candidates"):
        raise ContractError("task.py current has unresolved task candidates")
    return value


def _ownership_task(payload: dict[str, Any]) -> tuple[str, str]:
    task = payload["work_context"].get("task")
    if not isinstance(task, dict):
        raise ContractError("handoff has no task ownership to transfer")
    task_id = safe_id(task.get("id"), "handoff task id")
    task_path = _text(task.get("path"), "handoff task path")
    if not task_path.startswith(".trellis/tasks/") or ".." in Path(task_path).parts:
        raise ContractError("handoff task path is unsafe")
    return task_id, task_path


def _direct_session_id(root: Path) -> str:
    source = _task_current(root).get("session_source")
    if not isinstance(source, str) or not source.startswith("session:"):
        raise ContractError("Trellis did not expose a direct session identity")
    return safe_id(source.removeprefix("session:"), "direct session id")


def _ownership_call(
    root: Path, operation: str, task_id: str, task_path: str, handoff_id: str,
    package_digest: str, expected_generation: Optional[int], *, explicit: bool,
    expected_continuity_digest: Optional[str] = None,
    include_current: bool = False,
    bind_package: bool = True,
) -> dict[str, Any]:
    script = _regular_file(root / ".trellis/scripts/task.py", "task.py")
    # The immutable package keeps its captured path; Trellis resolves moved tasks.
    task_ref = task_path if (root / task_path).exists() else Path(task_path).name
    command = [
        sys.executable, str(script), "transfer", operation,
        "--task-id", task_id, "--task-path", task_ref,
    ]
    if bind_package:
        command += ["--package-id", handoff_id, "--package-digest", package_digest]
    if expected_generation is not None:
        command += ["--expected-generation", str(expected_generation)]
    if expected_continuity_digest is not None:
        command += ["--expected-continuity-digest", expected_continuity_digest]
    if explicit:
        command.append("--explicit-user-request")
    if include_current:
        command.append("--include-current")
    result = subprocess.run(
        command, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=20, check=False,
    )
    try:
        value = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Trellis task transfer returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("Trellis task transfer returned invalid JSON")
    if contains_secret(value):
        raise ContractError("Trellis task transfer returned unsafe data")
    if result.returncode:
        reason = _text(value.get("reason"), "transfer failure") if value.get("reason") else "unknown failure"
        code = _text(value.get("code"), "transfer failure code") if value.get("code") else "unknown"
        raise ContractError("Trellis task transfer %s withheld (%s): %s" % (operation, code, reason))
    return value


def _ownership_event(root: Path, handoff_id: str, operation: str, result: dict[str, Any], *, intent: Optional[dict] = None) -> dict[str, Any]:
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    if not events:
        raise ContractError("handoff lifecycle is not prepared")
    state = _state(events)
    refs = [
        "ownership_status=" + _text(result.get("status"), "ownership.status"),
        "ownership_generation=" + str(result.get("generation")),
    ]
    if intent is not None:
        refs += ["operation_intent=" + storage.digest(intent), "operation_session=" + intent["session"], "expected_generation=" + str(intent["expected_generation"]), "package_digest=" + intent["package_digest"]]
        if intent["expected_continuity_digest"] is not None:
            refs.append("expected_continuity_digest=" + intent["expected_continuity_digest"])
    receipt = _append_event(
        root, handoff_id, "ownership_" + operation,
        {"source": state["source"], "target": state["target"], "retention": state["retention"]},
        refs, operation_intent=intent,
    )
    return {"ownership": result, "lifecycle": receipt}


def _ownership_gate(root: Path, mode: str, state: dict[str, str], observation: Optional[str]) -> None:
    lifecycle_mode(mode)
    if not _source_ready(mode, state):
        raise ContractError("handoff source boundary is not sealed")


def ownership_operation(root: Path, operation: str, handoff_path: str, *, explicit: bool, archive_observation: Optional[str] = None, expected_generation: Optional[int] = None, expected_continuity_digest: Optional[str] = None, include_current: bool = False) -> dict[str, Any]:
    handoff_id, core, payload = _core(root, handoff_path, mutable=operation != "status")
    task_id, task_path = _ownership_task(payload)
    package_digest = _ownership_core_digest(core).removeprefix("sha256:")
    if operation == "status":
        result = _ownership_call(root, operation, task_id, task_path, handoff_id, package_digest, None, explicit=False, include_current=include_current)
        intent_path = core.parent / storage.OWNERSHIP_INTENT
        return {"handoff_id": handoff_id, "ownership": result, "pending_operation": _read_ownership_intent(intent_path, handoff_id)}
    if not explicit:
        raise ContractError("ownership writes require --explicit-user-request")
    if operation not in {"quiesce", "seal", "retire", "claim", "consume", "release"}:
        raise ContractError("task transfer operation is unsupported")
    if expected_continuity_digest is not None:
        if operation != "claim" or not re.fullmatch(r"[a-f0-9]{64}", expected_continuity_digest):
            raise ContractError("claim requires a valid expected live SHA-256 digest")
    generation = 0 if operation == "quiesce" and expected_generation is None else expected_generation
    if generation is None:
        raise ContractError("expected ownership generation is required")
    _integer(generation, "expected ownership generation")
    if operation == "quiesce":
        current = _task_current(root).get("current_task")
        if not isinstance(current, dict) or current.get("id") != task_id or current.get("dir") != task_path:
            raise ContractError("source task is not the direct current task")
        _direct_session_id(root)
    if operation == "retire":
        events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
        _ownership_gate(root, _prepared_mode(events), _state(events), archive_observation or "not_required")
    captured = payload["work_context"]["task"]["continuity"]["source_digest"]
    recovering_pointer = False
    previous = None
    if operation in {"claim", "retire"}:
        previous = _ownership_call(root, "status", task_id, task_path, handoff_id, package_digest, None, explicit=False)
        if captured is not None and previous.get("continuity_digest") != captured:
            raise ContractError("Trellis ownership no longer matches the immutable package source digest")
        recovery_states = {"claiming", "recovery_required"} if operation == "claim" else {"retiring", "recovery_required"}
        identity_field = "target_session_id" if operation == "claim" else "source_session_id"
        recovering_pointer = (
            operation in {"claim", "retire"} and previous.get("status") in recovery_states
            and previous.get("generation") == generation
            and previous.get(identity_field) == _direct_session_id(root)
        )
    if previous is None:
        previous = _ownership_call(root, "status", task_id, task_path, handoff_id, package_digest, None, explicit=False)
    receipt_path = _lifecycle_path(root, handoff_id)
    _regular_file(receipt_path, "prepared lifecycle receipt")
    receipt_fingerprint = storage.fingerprint(receipt_path, content=False)
    if not _read_events(receipt_path, handoff_id):
        raise ContractError("handoff lifecycle is not prepared")
    core_fingerprint = storage.fingerprint(core, content=False)
    intent_path = core.parent / storage.OWNERSHIP_INTENT
    request_identity = {"schema_version": 1, "kind": "pennix-handoff-ownership-intent", "handoff_id": handoff_id, "operation": operation, "session": _direct_session_id(root), "package_digest": package_digest, "expected_generation": generation, "expected_continuity_digest": captured if operation == "quiesce" else expected_continuity_digest}
    pending = _read_ownership_intent(intent_path, handoff_id)
    if pending and {key: pending.get(key) for key in request_identity} != request_identity:
        # Only native recovery evidence can fence a different session's unfinished claim.
        recovered = (
            pending["operation"] == "claim"
            and previous.get("package_id") == handoff_id and previous.get("package_digest") == pending["package_digest"]
            and type(previous.get("generation")) is int and previous["generation"] > pending["expected_generation"] + 1
            and any(isinstance(item, dict) and item.get("target_session_id") == pending["session"] and item.get("generation") == pending["expected_generation"] + 1 for item in previous.get("recovery_history", []))
        )
        if recovered:
            _ownership_event(root, handoff_id, "recovered_observation", previous, intent=pending)
            with storage.lock(root):
                if _read_ownership_intent(intent_path, handoff_id) != pending:
                    raise ContractError("handoff recovery intent changed")
                intent_path.unlink()
                storage.fsync_directory(core.parent)
            receipt_fingerprint = storage.fingerprint(receipt_path, content=False)
    resuming_intent = False
    with storage.lock(root):
        if storage.zip_path(root, handoff_id).exists() or storage.fingerprint(core, content=False) != core_fingerprint or storage.fingerprint(receipt_path, content=False) != receipt_fingerprint:
            raise ContractError("handoff source changed before native ownership operation")
        if intent_path.exists():
            intent = _read_ownership_intent(intent_path, handoff_id)
            if {key: intent.get(key) for key in request_identity} != request_identity:
                raise ContractError("another handoff ownership operation requires recovery")
            resuming_intent = True
        else:
            intent = {**request_identity, "native_before_digest": storage.digest(previous), "receipt_fingerprint": receipt_fingerprint}
            storage.atomic_record(intent_path, intent)
    try:
        completed_states = {"quiesce": "quiescing", "seal": "sealed", "retire": "ready", "claim": "claimed", "consume": "consumed"}
        actor_field = "target_session_id" if operation in {"claim", "consume"} else "source_session_id"
        completed = (
            resuming_intent and previous.get("status") == completed_states.get(operation)
            and previous.get("generation") == generation + (0 if recovering_pointer else 1)
            and previous.get("package_id") == handoff_id and previous.get("package_digest") == package_digest
            and previous.get(actor_field) == intent["session"]
            and (intent["expected_continuity_digest"] is None or previous.get("target_continuity_digest", previous.get("continuity_digest")) == intent["expected_continuity_digest"])
        )
        if resuming_intent and operation == "release" and previous.get("status") == "absent":
            current = _task_current(root)
            selected = current.get("current_task")
            if current.get("source") != "session:" + intent["session"] or not isinstance(selected, dict) or selected.get("id") != task_id or selected.get("dir") != task_path:
                raise ContractError("release recovery requires the source's direct native task pointer")
            result = {"status": "release_observed", "generation": generation, "task_id": task_id, "observation": "native ownership absent; direct source task pointer present"}
        elif completed:
            result = previous
        else:
            result = _ownership_call(
                root, operation, task_id, task_path, handoff_id, package_digest, generation,
                explicit=True,
                expected_continuity_digest=captured if operation == "quiesce" else expected_continuity_digest,
            )
    except ContractError:
        try:
            unchanged = storage.digest(_ownership_call(root, "status", task_id, task_path, handoff_id, package_digest, None, explicit=False)) == intent["native_before_digest"]
            with storage.lock(root):
                if unchanged and _read_ownership_intent(intent_path, handoff_id) == intent and storage.fingerprint(receipt_path, content=False) == intent["receipt_fingerprint"]:
                    intent_path.unlink()
                    storage.fsync_directory(core.parent)
        except (ContractError, OSError):
            pass
        raise
    if operation != "release" and result.get("generation") != generation + (0 if recovering_pointer else 1):
        raise ContractError("Trellis task transfer returned an unexpected generation")
    receipt = _ownership_event(root, handoff_id, operation, result, intent=intent)
    if operation == "seal" and result.get("status") == "sealed":
        state = _state(_read_events(_lifecycle_path(root, handoff_id), handoff_id))
        receipt["boundary"] = _append_event(
            root, handoff_id, "boundary_sealed",
            {"source": "boundary_sealed", "target": state["target"], "retention": state["retention"]},
            ["trellis_seal=" + handoff_id],
            operation_intent=intent,
        )
    with storage.lock(root):
        if _read_ownership_intent(intent_path, handoff_id) != intent:
            raise ContractError("handoff ownership intent changed before completion")
        intent_path.unlink()
        storage.fsync_directory(core.parent)
    return {"handoff_id": handoff_id, **receipt}










def _lifecycle_result(operation: str, handoff_id: str, result: dict[str, Any]) -> None:
    emit(operation, result["status"], handoff_id=handoff_id, **{key: value for key, value in result.items() if key not in {"status", "handoff_id"}})


def lifecycle_prepare(root: Path, handoff_path: str, mode: str) -> tuple[str, dict[str, Any]]:
    handoff_id, _, payload = _core(root, handoff_path, mutable=True)
    selected_mode = lifecycle_mode(mode)
    observation = _continuity_observation(root, payload["work_context"]["task"])
    return handoff_id, _append_event(
        root, handoff_id, "prepare",
        {"source": "prepared", "target": "not_admitted", "retention": "none"},
        ["mode=" + selected_mode, "source=session:" + _direct_session_id(root)],
        cr_observation=observation,
    )


def lifecycle_seal(root: Path, handoff_path: str, *, explicit: bool) -> tuple[str, dict[str, Any]]:
    if not explicit:
        raise ContractError("taskless seal requires --explicit-user-request")
    handoff_id, _, payload = _core(root, handoff_path, mutable=True)
    _read_paired_prompt(root, handoff_path)
    if payload["work_context"]["task"] is not None:
        raise ContractError("task-bearing handoff must use native ownership seal")
    current = _task_current(root)
    if current["current_task"] is not None or current.get("source") != "none":
        raise ContractError("taskless seal requires an unambiguous taskless current session")
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    prepare = next((event for event in events if event["event_type"] == "prepare"), None)
    source = "source=session:" + _direct_session_id(root)
    if prepare is None or source not in prepare["evidence_refs"]:
        raise ContractError("taskless seal must run in the prepared source session")
    state = _state(events)
    return handoff_id, _append_event(root, handoff_id, "boundary_sealed", {**state, "source": "boundary_sealed"}, ["taskless_seal=" + handoff_id, source])


def lifecycle_finalize(root: Path, handoff_path: str, observation_path: str) -> tuple[str, dict[str, Any]]:
    observation = validate_observation(load_json_file(_project_file(root, observation_path, "observation path")))
    return lifecycle_finalize_observation(root, handoff_path, observation, "observation=" + observation_path)


def lifecycle_finalize_observation(root: Path, handoff_path: str, observation: dict[str, Any], evidence_ref: str) -> tuple[str, dict[str, Any]]:
    handoff_id, _, payload = _core(root, handoff_path, mutable=True)
    _read_paired_prompt(root, handoff_path)
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    if not events:
        raise ContractError("handoff lifecycle is not prepared")
    lifecycle_mode(_prepared_mode(events))
    observation = validate_observation(observation)
    status = "pending"
    if observation["availability"] == "unsupported":
        status = "unsupported"
    elif observation["availability"] == "unavailable":
        status = "unavailable"
    elif observation["boundary"]["status"] == "sealed":
        status = "boundary_sealed"
    if status == "pending" and _state(events)["source"] == "boundary_sealed":
        status = _state(events)["source"]
    result = _append_event(root, handoff_id, "finalize", {"source": status, "target": _state(events)["target"], "retention": _state(events)["retention"]}, [evidence_ref])
    return handoff_id, result


def lifecycle_admit(root: Path, handoff_path: str, attestation_path: str) -> tuple[str, dict[str, Any]]:
    handoff_id, _, payload = _core(root, handoff_path, mutable=True)
    _read_paired_prompt(root, handoff_path)
    attestation = validate_attestation(load_json_file(_project_file(root, attestation_path, "attestation path")))
    _validate_history_reading(root, payload, attestation)
    rollout_session = payload["source"]["rollout"].get("session_id")
    if rollout_session is not None and attestation["target_source"] == "session:" + rollout_session:
        raise ContractError("target source cannot reuse the handoff source session id")
    current = _task_current(root)
    if current.get("session_source") != attestation["target_source"]:
        raise ContractError("target source is not the current direct session source")
    events = _read_events(_lifecycle_path(root, handoff_id), handoff_id)
    current_state = _state(events)
    if not events:
        raise ContractError("handoff lifecycle is not prepared")
    if any("source=" + attestation["target_source"] in event["evidence_refs"] for event in events if event["event_type"] == "prepare"):
        raise ContractError("target source cannot reuse the prepared source session id")
    target_source = attestation["target_source"]
    steps = _attestation_steps(attestation)
    attempt_target = _consumption_attempt_target(events)
    if attempt_target is not None and attempt_target != target_source:
        raise ContractError("handoff asset has already been consumed by another target")
    if current_state["target"] == "reconciled" and attempt_target == target_source:
        return handoff_id, {"status": "idempotent", "state": current_state, "target": target_source}
    source_ready = _source_ready(_prepared_mode(events), current_state) and _source_task_ready(payload, events)
    if not source_ready:
        return handoff_id, {"status": "pending", "state": current_state}
    if steps != CONSUMPTION_STEPS:
        return handoff_id, {"status": "incomplete", "state": current_state, "target": target_source}
    result = _append_event(
        root, handoff_id, "admit",
        {"source": current_state["source"], "target": "reconciled", "retention": "archive_eligible"},
        ["target=" + target_source, "steps=" + ",".join(steps), "history_read=" + attestation["history_read"],
         "history_refs=" + json.dumps(attestation["history_refs"], ensure_ascii=True, sort_keys=True, separators=(",", ":"))],
    )
    return handoff_id, result


def _retention_observation(root: Path, identifier: str, core: Path, identity: dict) -> dict:
    context = identity.get("work_context")
    if not isinstance(context, dict) or "task" not in context:
        raise ContractError("historical task association is unknown")
    if context["task"] is None:
        return {"status": "not_applicable"}
    task_id, task_path = _ownership_task(identity)
    return _ownership_call(root, "status", task_id, task_path, identifier, _ownership_core_digest(core).removeprefix("sha256:"), None, explicit=False, include_current=True, bind_package=False)


def inspect_handoff(root: Path, handoff_path: str) -> dict:
    identifier, _ = _destination(root, handoff_path=handoff_path)
    with storage.open_package(root, identifier) as (directory, kind):
        core = directory / HANDOFF_NAME
        identity = storage.historical_identity(core)
        if identity.get("handoff_id") != identifier or identity.get("kind") != KIND:
            raise ContractError("historical package identity differs")
        project = identity.get("project")
        if not isinstance(project, dict) or project.get("name") != root.name:
            raise ContractError("historical project association differs")
        version = identity.get("schema_version")
        current = type(version) is int and version == SCHEMA_VERSION
        if current:
            validate(root, load_json_file(core), identifier, directory / HISTORY_NAME)
        elif type(version) is not int or version not in {4, 6, 8, 9, 11}:
            raise ContractError("historical schema is unknown")
        receipt = directory / storage.LIFECYCLE
        if not receipt.exists():
            receipt = _lifecycle_path(root, identifier)
        historical: dict = {"status": "absent"}
        blockers = []
        intent_path = directory / storage.OWNERSHIP_INTENT
        pending_operation = _read_ownership_intent(intent_path, identifier)
        if pending_operation is not None:
            blockers.append("A handoff ownership operation has unresolved local intent")
        try:
            events = _read_events(receipt, identifier)
            if events:
                state = _state(events)
                historical = {"status": "recorded", "state": state}
                if current and (state["source"] != "boundary_sealed" or state["target"] != "reconciled" or state["retention"] not in {"archive_eligible", "archived", "retained", "restored", "reopened", "purged"}):
                    blockers.append("Current handoff has incomplete boundary/consumption")
            elif current:
                blockers.append("Current handoff has no committed lifecycle evidence")
        except ContractError:
            if current:
                raise
            historical = {"status": "historical_original_uninterpreted"}
        try:
            observation = _retention_observation(root, identifier, core, identity)
            if observation.get("package_id", identifier) == identifier and observation.get("status") not in {"absent", "consumed", "released", "not_applicable"}:
                blockers.append("This handoff still has a pending native ownership operation")
        except ContractError as exc:
            observation = {"status": "unknown", "reason": str(exc)}
            blockers.append("Cannot verify current task ownership/recovery dependencies")
        if current and not (directory / "session-handoff-prompt.md").is_file():
            blockers.append("Current handoff paired prompt is missing")
        elif current:
            _read_paired_prompt_directory(directory)
        return {
            "handoff_id": identifier, "storage_integrity": {"status": "verified", "kind": kind, "schema_version": version, "level": "current_schema" if current else "original_bytes_and_identity_projection"},
            "historical_lifecycle": historical,
            "current_admission": {"status": "requires_native_current_checks" if current and kind == "plain" else "not_applicable", "restores_authority": False},
            "current_task_observation": observation,
            "qualification": {"kind": "current_lifecycle" if current else "historical_readonly", "basis": ["original identity", "native current ownership observation", "exact retention approval"], "eligible": not blockers},
            "blockers": blockers,
            "storage_operation": storage.last_operation(directory / storage.JOURNAL, identifier),
            "pending_operation": pending_operation,
            "missing": sorted(storage.PRIMARY - {member.name for member in directory.iterdir()}),
        }


def _storage_event(path: Path, identifier: str, action: str, retention: str, content_digest: str) -> None:
    events = _read_events(path, identifier)
    state = _state(events)
    if not _transition("retention", state["retention"], retention):
        raise ContractError("retention transition is invalid")
    event = {
        "schema_version": LIFECYCLE_SCHEMA_VERSION, "kind": LIFECYCLE_EVENT_KIND,
        "handoff_id": identifier, "event_type": action,
        "source_status": state["source"], "target_status": state["target"],
        "retention_status": retention,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "actor": LIFECYCLE_ACTOR, "evidence_refs": ["content_sha256=" + content_digest],
    }
    _event_shape(event, identifier)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _retention_members(root: Path, identifier: str, private: Path) -> tuple[dict[str, Path], Optional[dict]]:
    archive = storage.zip_path(root, identifier)
    manifest = storage.extract(archive, identifier, private) if archive.exists() else None
    members = {name: private / name for name in manifest["members"]} if manifest else {}
    for name, source in storage.sources(root, identifier).items():
        target = private / name
        if name in members:
            if name in storage.CONTROLS:
                if storage.is_prefix(source, target):
                    continue
                if not storage.is_prefix(target, source):
                    raise ContractError("handoff lifecycle copies diverge")
            elif storage.fingerprint(source)[-1] != storage.fingerprint(target)[-1]:
                raise ContractError("existing ZIP differs from original source")
            else:
                continue
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        os.chmod(target, 0o600)
        members[name] = target
    return members, manifest


def _publish_storage(candidate: Path, archive: Path) -> None:
    os.replace(candidate, archive)
    storage.fsync_directory(archive.parent)


def _purge_tombstone(root: Path, identifier: str, tombstone: Path, approved: list[dict]) -> None:
    canonical = storage.package_directory(root, identifier)
    storage.safe_path(root, tombstone)
    if tombstone.parent != canonical.parent or not re.fullmatch(r"\." + re.escape(identifier) + r"\.purge-[0-9a-f]{16}", tombstone.name):
        raise ContractError("purge intent tombstone is outside its exact owner scope")
    if not tombstone.exists():
        return
    expected = {Path(item["path"]).relative_to(canonical.relative_to(root)).as_posix(): item["fingerprint"] for item in approved if (root / item["path"]).is_relative_to(canonical)}
    entries = list(itertools.islice(tombstone.rglob("*"), storage.MAX_MEMBERS * 2 + 1))
    if len(entries) > storage.MAX_MEMBERS * 2:
        raise ContractError("purge tombstone member budget exceeded")
    directories = {parent.as_posix() for name in expected for parent in Path(name).parents if parent != Path(".")}
    files = []
    for member in entries:
        storage.safe_path(root, member)
        name = member.relative_to(tombstone).as_posix()
        if member.is_dir():
            if name not in directories:
                raise ContractError("purge tombstone contains an unknown directory")
        elif name not in expected or storage.fingerprint(member, content=False) != expected[name][:5]:
            raise ContractError("purge tombstone contains changed or unknown evidence")
        else:
            files.append(member)
    with storage.lock(root):
        for member in files:
            if storage.fingerprint(member, content=False) != expected[member.relative_to(tombstone).as_posix()][:5]:
                raise ContractError("purge tombstone changed before unlink")
            member.unlink()
        for member in sorted((item for item in entries if item.is_dir()), key=lambda item: len(item.parts), reverse=True):
            member.rmdir()
        tombstone.rmdir()
        storage.fsync_directory(tombstone.parent)


def _checked_recovery_sources(root: Path, identifier: str, operation: dict) -> list[dict]:
    sources = operation.get("sources")
    if not isinstance(sources, list) or len(sources) > storage.MAX_MEMBERS:
        raise ContractError("purge intent source set is invalid")
    archive_path = storage.zip_path(root, identifier)
    manifest = storage.verify(archive_path, identifier)
    for item in sources:
        if not isinstance(item, dict) or set(item) != {"path", "fingerprint"} or not isinstance(item["path"], str):
            raise ContractError("purge intent source identity is invalid")
        path = storage.safe_path(root, root / item["path"])
        relative = path.relative_to(root).parts
        canonical = storage.package_directory(root, identifier)
        member = None
        if path.is_relative_to(canonical):
            name = path.relative_to(canonical).as_posix()
            if name in storage.PRIMARY | storage.CONTROLS or name.startswith("legacy/"):
                member = name
        elif relative == (".trellis", ".runtime", "handoff-lifecycle", identifier + ".jsonl"):
            member = "legacy/handoff-lifecycle/" + relative[-1]
        elif relative[:4] == (".trellis", ".runtime", "handoff-archive", identifier) and len(relative) == 5 and relative[-1] in storage.PRIMARY:
            member = "legacy/handoff-archive/" + relative[-1]
        elif relative[:3] == (".trellis", ".runtime", "handoff-ownership") and len(relative) == 5 and relative[-1] == identifier + ".json":
            member = "legacy/handoff-ownership/" + "/".join(relative[-2:])
        record = item["fingerprint"]
        if member not in manifest["members"] or not isinstance(record, list) or len(record) != 6 or not all(type(value) is int for value in record[:5]) or record[2] < 0 or not isinstance(record[-1], str) or not re.fullmatch(r"[a-f0-9]{64}", record[-1]):
            raise ContractError("purge intent source is outside its exact owner scope")
        stored = manifest["members"][member]
        if member not in storage.CONTROLS:
            if stored["bytes"] != record[2] or stored["sha256"] != record[-1]:
                raise ContractError("purge source is not preserved by the verified ZIP")
        else:
            if record[2] > stored["bytes"]:
                raise ContractError("purge control prefix exceeds the verified ZIP")
            hasher, remaining = hashlib.sha256(), record[2]
            with zipfile.ZipFile(archive_path) as archive, archive.open(member) as handle:
                while remaining:
                    chunk = handle.read(min(storage.CHUNK, remaining))
                    if not chunk:
                        raise ContractError("purge control prefix is incomplete")
                    hasher.update(chunk)
                    remaining -= len(chunk)
            if hasher.hexdigest() != record[-1]:
                raise ContractError("purge control source differs from preserved prefix")
    return sources


def _tombstone_observation(root: Path, identifier: str, tombstone: Path) -> dict | None:
    if tombstone.parent != storage.package_directory(root, identifier).parent or not re.fullmatch(r"\." + re.escape(identifier) + r"\.purge-[0-9a-f]{16}", tombstone.name):
        raise ContractError("purge observation is outside its exact owner scope")
    if not tombstone.exists():
        return None
    storage.safe_path(root, tombstone)
    entries = list(itertools.islice(tombstone.rglob("*"), storage.MAX_MEMBERS * 2 + 1))
    if len(entries) > storage.MAX_MEMBERS * 2:
        raise ContractError("purge recovery member budget exceeded")
    result = {}
    for entry in entries:
        storage.safe_path(root, entry)
        result[entry.relative_to(tombstone).as_posix()] = {"kind": "directory"} if entry.is_dir() else storage.fingerprint(entry)
    return result


def lifecycle_retention(root: Path, action: str, handoff_path: str, confirmation: Optional[str] = None, confirm: Optional[str] = None) -> tuple[str, dict[str, Any]]:
    identifier, core = _destination(root, handoff_path=handoff_path)
    if action not in {"archive", "purge", "restore", "reopen"}:
        raise ContractError("retention action is unsupported")
    if confirmation is not None and confirmation != identifier:
        raise ContractError("exact handoff id confirmation differs")
    inspection = inspect_handoff(root, handoff_path)
    before = storage.snapshot(root, identifier)
    archive = storage.zip_path(root, identifier)
    previous = storage.verify(archive, identifier) if archive.exists() else None
    blockers = list(inspection["blockers"])
    if action in {"purge", "restore"} and previous is None:
        # A unique old archive must first be preserved as the complete ZIP unit.
        blockers.append("Create and verify the lossless ZIP before source exit or restore")
    if action == "reopen" and not core.exists():
        blockers.append("Restore the expanded package before reopening storage")
    approved_sources = [
        {"path": path.relative_to(root).as_posix(), "fingerprint": before["files"][name]}
        for name, path in storage.sources(root, identifier).items()
    ]
    approved_sources = list({item["path"]: item for item in approved_sources}.values())
    preview = {"handoff_id": identifier, "action": action, "inspection": inspection, "snapshot": before, "sources": approved_sources, "target": archive.relative_to(root).as_posix(), "blockers": blockers, "eligible": not blockers, "removes_sources": action == "purge", "restores_authority": False}
    last_operation = inspection["storage_operation"] or {}
    restored = last_operation.get("action") == "restore" and last_operation.get("status") == "complete"
    recovery = previous is not None and previous["operation"].get("action") == "purge" and previous["operation"].get("status") == "intent" and not restored
    pending_tombstones = last_operation.get("pending_tombstones", []) if restored else []
    if not isinstance(pending_tombstones, list) or len(pending_tombstones) > storage.MAX_MEMBERS:
        raise ContractError("pending recovery proof is invalid")
    if recovery:
        original_sources = _checked_recovery_sources(root, identifier, previous["operation"])
        tombstone = storage.safe_path(root, root / previous["operation"].get("tombstone", ""))
        if tombstone.parent != core.parent.parent or not re.fullmatch(r"\." + re.escape(identifier) + r"\.purge-[0-9a-f]{16}", tombstone.name):
            raise ContractError("purge recovery tombstone identity is invalid")
        preview["recovery_intent"] = previous["operation"]
        preview["tombstone"] = _tombstone_observation(root, identifier, tombstone)
        if action == "restore" and tombstone.exists():
            pending_tombstones = [{"path": tombstone.relative_to(root).as_posix(), "sources": original_sources}]
        if action == "purge":
            approved_sources = original_sources
            preview["sources"] = approved_sources
    if pending_tombstones:
        preview["pending_tombstones"] = [{**item, "observation": _tombstone_observation(root, identifier, storage.safe_path(root, root / item["path"]))} for item in pending_tombstones]
    preview_digest = storage.digest(preview)
    preview.update({"status": "preview", "digest": preview_digest})
    if confirm is None:
        return identifier, preview
    if confirmation != identifier or confirm != preview_digest:
        raise ContractError("retention preview changed; exact ID and fresh digest are required")
    if blockers:
        raise ContractError("retention is protected: " + "; ".join(blockers))
    base = storage.package_directory(root, identifier).parent
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="." + identifier + ".retention-", dir=base) as temporary:
        private = Path(temporary)
        expanded = private / "package"
        expanded.mkdir(mode=0o700)
        members, old = _retention_members(root, identifier, expanded)
        originals = {name: [storage.fingerprint(path)[2], storage.fingerprint(path)[-1]] for name, path in members.items() if name not in storage.CONTROLS}
        content_digest = storage.digest(originals)
        lifecycle = members.get(storage.LIFECYCLE)
        input_digest = storage.fingerprint(lifecycle)[-1] if lifecycle else None
        current = inspection["qualification"]["kind"] == "current_lifecycle"
        operation = {"action": action, "status": "complete", "sources": approved_sources, "observed_at": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
        if pending_tombstones:
            operation["pending_tombstones"] = pending_tombstones
        candidate = private / "candidate.zip"
        canonical = storage.package_directory(root, identifier)
        tombstone = root / old["operation"]["tombstone"] if recovery else base / ("." + identifier + ".purge-" + preview_digest[:16])

        def prepare_zip():
            journal = expanded / storage.JOURNAL
            storage.append_operation(journal, identifier, operation)
            members[storage.JOURNAL] = journal
            locations = {name: path.relative_to(root).as_posix() for name, path in storage.sources(root, identifier).items()}
            for name in members:
                if name not in locations:
                    locations[name] = old["members"][name]["source"] if old and name in old["members"] else (canonical / name).relative_to(root).as_posix()
            return storage.write(candidate, identifier, members, root, qualification=inspection["qualification"], operation=operation, input_lifecycle_digest=input_digest, source_locations=locations)

        def prepare_mirrors():
            mirrors = {}
            for name in storage.CONTROLS:
                if name in members:
                    mirror = private / name
                    shutil.copyfile(members[name], mirror)
                    os.chmod(mirror, 0o600)
                    with mirror.open("rb") as handle:
                        os.fsync(handle.fileno())
                    mirrors[name] = mirror
            return mirrors

        def publish_mirrors(mirrors):
            for name, mirror in mirrors.items():
                os.replace(mirror, canonical / name)
            storage.fsync_directory(canonical)

        def recheck():
            if _retention_observation(root, identifier, expanded / HANDOFF_NAME, storage.historical_identity(expanded / HANDOFF_NAME)) != inspection["current_task_observation"]:
                raise ContractError("native task ownership changed after preview")

        if action == "archive" and old is not None:
            # ZIP publication already committed the archive; repair only its prefix mirror.
            recheck()
            mirrors = prepare_mirrors()
            with storage.lock(root):
                storage.unchanged(root, identifier, before)
                if canonical.is_dir():
                    publish_mirrors(mirrors)
                storage.fsync_directory(base)
            return identifier, {"status": "idempotent", "digest": preview_digest, "source_retained": True, "zip_verified": True}

        if action == "restore":
            if canonical.exists():
                return identifier, {"status": "idempotent", "source_retained": True, "restores_authority": False}
            if current and lifecycle:
                _storage_event(lifecycle, identifier, "restore", "restored", content_digest)
            storage.append_operation(expanded / storage.JOURNAL, identifier, operation)
            recheck()
            # The complete private package includes all raw legacy proof members.
            for directory, _, _ in os.walk(expanded, topdown=False):
                storage.fsync_directory(Path(directory))
            with storage.lock(root):
                storage.unchanged(root, identifier, before)
                if canonical.exists():
                    raise ContractError("restore target appeared after preview")
                os.rename(expanded, canonical)
                storage.fsync_directory(base)
            return identifier, {"status": "recorded", "action": action, "zip_retained": True, "restores_authority": False}

        if action == "reopen":
            if current and lifecycle:
                _storage_event(lifecycle, identifier, "reopen", "reopened", content_digest)
            journal = expanded / storage.JOURNAL
            storage.append_operation(journal, identifier, operation)
            members[storage.JOURNAL] = journal
            recheck()
            mirrors = prepare_mirrors()
            with storage.lock(root):
                storage.unchanged(root, identifier, before)
                publish_mirrors(mirrors)
            return identifier, {"status": "recorded", "action": action, "restores_authority": False}

        if action == "archive":
            if current and lifecycle:
                _storage_event(lifecycle, identifier, "archive", "archived", content_digest)
            prepare_zip()
            mirrors = prepare_mirrors()
            recheck()
            with storage.lock(root):
                storage.unchanged(root, identifier, before)
                _publish_storage(candidate, archive)
                if canonical.is_dir():
                    publish_mirrors(mirrors)
            return identifier, {"status": "recorded", "action": action, "zip_verified": True, "source_retained": True, "net_released_bytes": 0}

        operation.update({"status": "intent", "tombstone": tombstone.relative_to(root).as_posix(), "content_digest": content_digest})
        if current and lifecycle and not recovery:
            _storage_event(lifecycle, identifier, "purge_intent", _state(_read_events(lifecycle, identifier))["retention"], content_digest)
        prepare_zip()
        recheck()
        with storage.lock(root):
            storage.unchanged(root, identifier, before)
            if tombstone.exists() and canonical.exists():
                raise ContractError("purge tombstone already exists; inspect recovery intent")
            _publish_storage(candidate, archive)
            if canonical.exists():
                os.rename(canonical, tombstone)
                storage.fsync_directory(base)
        intent_fingerprint = storage.fingerprint(archive)
        try:
            for item in pending_tombstones:
                old_sources = _checked_recovery_sources(root, identifier, {"sources": item["sources"]})
                _purge_tombstone(root, identifier, root / item["path"], old_sources)
            if tombstone.exists():
                _purge_tombstone(root, identifier, tombstone, approved_sources)
            for item in approved_sources:
                source = storage.safe_path(root, root / item["path"])
                if source.is_relative_to(canonical) or not source.exists():
                    continue
                if storage.fingerprint(source) != item["fingerprint"]:
                    raise ContractError("legacy source changed after purge intent; retained")
                source.unlink()
                storage.fsync_directory(source.parent)
            if current and lifecycle:
                _storage_event(lifecycle, identifier, "purge", "purged", content_digest)
            operation["status"] = "complete"
            prepare_zip()
            with storage.lock(root):
                if storage.fingerprint(archive, content=False) != intent_fingerprint[:5]:
                    raise ContractError("purge intent ZIP changed before completion")
                _publish_storage(candidate, archive)
        except (Exception, KeyboardInterrupt) as exc:
            raise ContractError("purge incomplete; verified ZIP and exact intent retained for restore/retry") from exc
        return identifier, {"status": "recorded", "action": action, "zip_retained": True, "sources_removed": [item["path"] for item in approved_sources], "restores_authority": False}




def lifecycle_status(root: Path, handoff_path: str) -> dict[str, Any]:
    handoff_id, destination = _destination(root, handoff_path=handoff_path)
    if storage.zip_path(root, handoff_id).exists() or (not destination.exists() and _archive_path(root, handoff_id).exists()):
        inspection = inspect_handoff(root, handoff_path)
        historical = inspection["historical_lifecycle"]
        return {"status": "pending", "handoff_id": handoff_id, "reason": "Archived history does not grant current admission", **inspection, **({"state": historical["state"]} if "state" in historical else {})}
    payload: Optional[Dict[str, Any]] = None
    if destination.exists():
        handoff_id, _, payload = _core(root, handoff_path)
    else:
        raise ContractError("handoff package is unavailable")
    path = _lifecycle_path(root, handoff_id)
    if not path.exists():
        return {"status": "absent", "handoff_id": handoff_id}
    events = _read_events(path, handoff_id)
    state = _state(events)
    mode = _prepared_mode(events)
    source_ready = _source_ready(mode, state) and (payload is None or _source_task_ready(payload, events))
    ownership: Optional[dict[str, Any]] = None
    if payload is not None and payload["work_context"]["task"] is not None:
        task_id, _ = _ownership_task(payload)
        core = destination if destination.exists() else _archive_path(root, handoff_id) / HANDOFF_NAME
        task = payload["work_context"]["task"]
        ownership = _ownership_call(
            root, "status", task_id, task["path"], handoff_id,
            _ownership_core_digest(core).removeprefix("sha256:"), None, explicit=False,
        )
        source_ready = (
            source_ready
            and ownership.get("status") in {"sealed", "ready", "claiming", "claimed", "consumed"}
            and (
                task["continuity"]["source_digest"] is None
                or ownership.get("continuity_digest") == task["continuity"]["source_digest"]
            )
        )
    prepare = next((event for event in events if event["event_type"] == "prepare"), None)
    cr_observation = {
        key: prepare[key]
        for key in ("cr_status", "cr_source_digest", "cr_observed_at", "cr_observation_state")
        if prepare is not None and key in prepare
    }
    return {
        "status": "ready" if source_ready else "pending", "handoff_id": handoff_id,
        "mode": mode, "state": state, **cr_observation,
        **({"ownership": ownership} if ownership is not None else {}),
    }


def emit(operation: str, status: str, reason: Optional[str] = None, **details: Any) -> None:
    result: Dict[str, Any] = {"operation": operation, "status": status, **details}
    if reason:
        result["reason"] = reason
    print(json.dumps(result, ensure_ascii=operation != "read", sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("resolve-rollout", help="Resolve the current Codex thread's rollout from read-only metadata")
    write = sub.add_parser("write")
    write.add_argument("--request", required=True, type=Path)
    write.add_argument("--explicit-user-request", action="store_true")
    check = sub.add_parser("validate")
    check.add_argument("--handoff", required=True)
    read = sub.add_parser("read")
    read.add_argument("--handoff", required=True)
    read.add_argument("--view", required=True, choices=("core", "history", "prompt"))
    read.add_argument("--event-index", type=int)
    read.add_argument("--offset", type=int, default=0)
    read.add_argument("--length", type=int, default=4096)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--handoff", required=True)
    prepare.add_argument("--mode", default="core_only", choices=sorted(LIFECYCLE_MODES))
    seal = sub.add_parser("seal")
    seal.add_argument("--handoff", required=True)
    seal.add_argument("--explicit-user-request", action="store_true")
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--handoff", required=True)
    finalize.add_argument("--observation", required=True)
    admit = sub.add_parser("admit")
    admit.add_argument("--handoff", required=True)
    admit.add_argument("--attestation", required=True)
    status = sub.add_parser("status")
    status.add_argument("--handoff", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--handoff", required=True)
    ownership = sub.add_parser("ownership")
    ownership_sub = ownership.add_subparsers(dest="ownership_command", required=True)
    for name in ("quiesce", "seal", "retire", "claim", "consume", "release", "status"):
        command = ownership_sub.add_parser(name)
        command.add_argument("--handoff", required=True)
        if name == "status":
            command.add_argument("--include-current", action="store_true")
        if name == "retire":
            command.add_argument("--archive-observation", choices=("not_required", "observed"), default="not_required")
        if name != "status":
            command.add_argument("--expected-generation", required=name != "quiesce", type=int)
        if name == "claim":
            command.add_argument("--expected-continuity-digest")
        if name != "status":
            command.add_argument("--explicit-user-request", action="store_true")
    retention = sub.add_parser("retention")
    retention.add_argument("action_positional", nargs="?", choices=("archive", "restore", "reopen", "purge"))
    retention.add_argument("--action", dest="action_option", choices=("archive", "restore", "reopen", "purge"))
    retention.add_argument("--handoff", required=True)
    retention.add_argument("--confirm-handoff-id")
    retention.add_argument("--confirm")
    args = parser.parse_args()
    try:
        root = _root(str(args.project_root))
        if args.command == "resolve-rollout":
            emit("resolve-rollout", "ready", rollout=resolve_rollout(), source="codex-state-5")
            return 0
        if args.command == "validate":
            handoff_id, destination = _destination(root, handoff_path=args.handoff)
            relative = destination.relative_to(root).as_posix()
            if not destination.exists() and not storage.zip_path(root, handoff_id).exists() and not _archive_path(root, handoff_id).exists():
                emit("validate", "absent", handoff_path=relative, handoff_id=handoff_id)
                return 2
            with storage.open_package(root, handoff_id) as (directory, kind):
                payload = load_json_file(directory / HANDOFF_NAME)
                status = validate(root, payload, handoff_id, directory / HISTORY_NAME)
            emit("validate", status, handoff_path=relative, handoff_id=handoff_id, storage_kind=kind)
            return 0 if status == "ready" else 2
        if args.command == "read":
            emit("read", "ready", **read_view(root, args.handoff, args.view, args.offset, args.length, args.event_index))
            return 0
        if args.command == "inspect":
            emit("inspect", "ready", **inspect_handoff(root, args.handoff))
            return 0
        if args.command == "prepare":
            handoff_id, result = lifecycle_prepare(root, args.handoff, args.mode)
            _lifecycle_result("prepare", handoff_id, result)
            return 0
        if args.command == "finalize":
            handoff_id, result = lifecycle_finalize(root, args.handoff, args.observation)
            _lifecycle_result("finalize", handoff_id, result)
            return 0
        if args.command == "seal":
            handoff_id, result = lifecycle_seal(root, args.handoff, explicit=args.explicit_user_request)
            _lifecycle_result("seal", handoff_id, result)
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
                expected_continuity_digest=getattr(args, "expected_continuity_digest", None),
                include_current=getattr(args, "include_current", False),
            )
            emit("ownership", "recorded", **result)
            return 0
        if args.command == "retention":
            action = args.action_positional or args.action_option
            if action is None:
                raise ContractError("retention action is required")
            handoff_id, result = lifecycle_retention(root, action, args.handoff, args.confirm_handoff_id, args.confirm)
            _lifecycle_result("retention", handoff_id, result)
            return 0
        if not args.explicit_user_request:
            raise ContractError("write requires --explicit-user-request")
        request = _request(root, args.request)
        handoff_id = _handoff_id()
        _, destination = _destination(root, create_id=handoff_id)
        if destination.parent.exists():
            raise ContractError("handoff package already exists: %s" % handoff_id)
        with tempfile.TemporaryDirectory(prefix="pennix-handoff-write-") as temporary:
            history = Path(temporary) / HISTORY_NAME
            payload = build(root, request, handoff_id, history)
            validate(root, payload, handoff_id, history)
            _atomic_json(destination, payload, history)
        emit("write", "ready", handoff_id=handoff_id, handoff_path=destination.relative_to(root).as_posix())
        return 0
    except (ContractError, OSError, UnicodeError, RecursionError, MemoryError, sqlite3.Error, subprocess.SubprocessError) as exc:
        reason = str(exc) if isinstance(exc, ContractError) else "handoff local I/O or native operation failed"
        emit(getattr(args, "command", "handoff"), "recovery_required", reason)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
