#!/usr/bin/env python3
"""Create and verify one explicit OpenViking handoff checkpoint."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import handoff  # noqa: E402
from workflow_contracts import ContractError, safe_id  # noqa: E402


KIND = "pennix-openviking-handoff-checkpoint"
SCHEMA_VERSION = 1
RUNTIME = ".trellis/.runtime/openviking-handoff"
STAGES = {"intent", "append_pending", "commit_pending", "archive_verified", "converged"}


class CheckpointError(RuntimeError):
    """Raised when OpenViking cannot provide the requested handoff evidence."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _path(root: Path, handoff_id: str) -> Path:
    safe_id(handoff_id, "handoff id")
    base = root / RUNTIME
    if base.is_symlink():
        raise CheckpointError("OpenViking checkpoint runtime is unsafe")
    return base / (handoff_id + ".json")


def _record_shape(value: Any, handoff_id: str, source_id: str) -> dict[str, Any]:
    required = {"schema_version", "kind", "handoff_id", "source_session_id", "openviking_session_id", "marker", "stage", "archive_uri", "task_id", "updated_at"}
    if not isinstance(value, dict) or set(value) != required:
        raise CheckpointError("OpenViking checkpoint receipt is invalid")
    if value["schema_version"] != SCHEMA_VERSION or value["kind"] != KIND or value["handoff_id"] != handoff_id:
        raise CheckpointError("OpenViking checkpoint receipt does not match the handoff")
    if value["source_session_id"] != source_id or value["openviking_session_id"] != "cx-" + source_id:
        raise CheckpointError("OpenViking checkpoint receipt does not match the source session")
    if value["marker"] != _marker(handoff_id) or value["stage"] not in STAGES:
        raise CheckpointError("OpenViking checkpoint receipt is invalid")
    for key in ("archive_uri", "task_id"):
        if value[key] is not None and (not isinstance(value[key], str) or not value[key]):
            raise CheckpointError("OpenViking checkpoint receipt is invalid")
    if not isinstance(value["updated_at"], str) or not value["updated_at"]:
        raise CheckpointError("OpenViking checkpoint receipt is invalid")
    return value


def _load(root: Path, handoff_id: str, source_id: str) -> dict[str, Any]:
    path = _path(root, handoff_id)
    if not path.exists():
        return {
            "schema_version": SCHEMA_VERSION, "kind": KIND, "handoff_id": handoff_id,
            "source_session_id": source_id, "openviking_session_id": "cx-" + source_id,
            "marker": _marker(handoff_id), "stage": "intent", "archive_uri": None,
            "task_id": None, "updated_at": _now(),
        }
    if path.is_symlink() or not path.is_file():
        raise CheckpointError("OpenViking checkpoint receipt is unsafe")
    try:
        return _record_shape(json.loads(path.read_text(encoding="utf-8")), handoff_id, source_id)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointError("OpenViking checkpoint receipt is unreadable") from exc


def _write(root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    path = _path(root, receipt["handoff_id"])
    receipt = dict(receipt)
    receipt["updated_at"] = _now()
    _record_shape(receipt, receipt["handoff_id"], receipt["source_session_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(receipt, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise CheckpointError("OpenViking checkpoint receipt could not be written") from exc
    return receipt


def _marker(handoff_id: str) -> str:
    return "[pennix-handoff-id:%s]" % handoff_id


def _last_json(raw: str, operation: str) -> dict[str, Any]:
    for line in reversed(raw.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise CheckpointError("ov %s returned no JSON object" % operation)


def _ov(*arguments: str, json_result: bool = True) -> dict[str, Any] | None:
    try:
        result = subprocess.run(["ov", *arguments, "-o", "json"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CheckpointError("ov %s is unavailable" % arguments[0]) from exc
    if result.returncode:
        raise CheckpointError("ov %s failed" % arguments[0])
    return _last_json(result.stdout, arguments[0]) if json_result else None


def _contains(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, dict):
        return any(_contains(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(_contains(item, needle) for item in value)
    return False


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _strings(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _strings(nested)]
    return []


def _objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value, *[item for nested in value.values() for item in _objects(nested)]]
    if isinstance(value, list):
        return [item for nested in value for item in _objects(nested)]
    return []


def _source(payload: dict[str, Any]) -> tuple[str, str]:
    raw = payload["source"]["rollout"].get("session_id")
    if raw is None:
        raise CheckpointError("archive-required handoff needs source rollout.session_id")
    source_id = safe_id(raw, "source rollout.session_id")
    return source_id, "cx-" + source_id


def _envelope(handoff_id: str, payload: dict[str, Any]) -> str:
    return "%s\n\nPennix formal handoff semantic checkpoint.\n\n%s" % (
        _marker(handoff_id), payload["memory_projection"]["semantic_capsule"],
    )


def _commit(value: dict[str, Any], source_session: str) -> tuple[str, str]:
    response = value.get("result") if isinstance(value.get("result"), dict) else value
    archive_uri = response.get("archive_uri")
    task_id = response.get("task_id")
    if response.get("archived") is not True or not isinstance(archive_uri, str) or not isinstance(task_id, str):
        raise CheckpointError("ov session commit did not return an archived handoff task")
    pattern = r"^viking://user/[^/]+/sessions/%s/history/archive_[^/]+$" % re.escape(source_session)
    if not re.fullmatch(pattern, archive_uri):
        raise CheckpointError("ov session commit returned an unexpected archive URI")
    return archive_uri, safe_id(task_id, "OpenViking task id")


def _verify_archive(archive_uri: str, marker: str) -> None:
    matches = _ov("grep", marker, "--uri", archive_uri)
    message_file = _ov("read", archive_uri + "/messages.jsonl")
    if not _contains(matches, marker) or not _contains(message_file, marker):
        raise CheckpointError("OpenViking archive does not contain the exact handoff marker")


def _archive_from_session(source_session: str, marker: str) -> str | None:
    details = _ov("session", "get", source_session)
    candidates = sorted({value for value in _strings(details) if "/history/archive_" in value})
    for archive_uri in candidates:
        try:
            _verify_archive(archive_uri, marker)
        except CheckpointError:
            continue
        return archive_uri
    return None


def _task_for_archive(archive_uri: str) -> str | None:
    tasks = _ov("task", "list", "--task-type", "session_commit")
    matches: set[str] = set()
    for item in _objects(tasks):
        result = item.get("result")
        if not isinstance(result, dict) or result.get("archive_uri") != archive_uri:
            continue
        task_id = item.get("task_id", item.get("id"))
        if isinstance(task_id, str):
            matches.add(safe_id(task_id, "OpenViking task id"))
    if len(matches) > 1:
        raise CheckpointError("OpenViking archive maps to multiple tasks")
    return next(iter(matches), None)


def _live_marker(source_session: str, marker: str) -> bool:
    try:
        context = _ov("session", "get-session-context", source_session)
    except CheckpointError:
        return False
    return _contains(context, marker)


def _converged(receipt: dict[str, Any]) -> bool:
    if not receipt["task_id"] or not receipt["archive_uri"]:
        return False
    task = _ov("task", "status", receipt["task_id"])
    if task.get("status") != "completed":
        return False
    result = task.get("result") if isinstance(task.get("result"), dict) else task
    if result.get("archive_uri") not in {None, receipt["archive_uri"]}:
        raise CheckpointError("OpenViking task archive does not match its checkpoint")
    memory_uri = result.get("memory_diff_uri")
    if memory_uri not in {None, receipt["archive_uri"] + "/memory_diff.json"}:
        raise CheckpointError("OpenViking task memory diff does not match its checkpoint")
    _ov("read", receipt["archive_uri"] + "/.done")
    _ov("read", receipt["archive_uri"] + "/memory_diff.json")
    return True


def _prepared(root: Path, handoff_path: str) -> tuple[str, dict[str, Any], dict[str, str]]:
    handoff_id, _, payload = handoff._core(root, handoff_path)
    events = handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)
    if not events:
        raise CheckpointError("handoff lifecycle is not prepared")
    mode = handoff._prepared_mode(events)
    if mode not in {"archive_required", "convergence_required"}:
        raise CheckpointError("OpenViking checkpoint is only needed for archive or convergence mode")
    handoff._direct_session_id(root)
    state = handoff._state(events)
    if payload["work_context"]["task"] is not None:
        if not handoff._source_task_ready(payload, events):
            raise CheckpointError("Trellis source ownership is not sealed")
        task_id, _ = handoff._ownership_task(payload)
        ownership = handoff._ownership_call(root, "status", task_id, handoff_id, handoff._ownership_core_digest(root / handoff_path), ["--json"], explicit=False)
        if ownership.get("status") != "sealed":
            raise CheckpointError("Trellis source ownership is not sealed")
    if state["source"] not in {"boundary_sealed", "pending", "archive_verified"}:
        raise CheckpointError("handoff source state cannot accept an OpenViking checkpoint")
    return handoff_id, payload, state


def _finalize(root: Path, handoff_path: str, payload: dict[str, Any], receipt: dict[str, Any], mode: str) -> dict[str, Any]:
    archive_uri = receipt["archive_uri"]
    if not archive_uri:
        raise CheckpointError("OpenViking archive is unavailable")
    complete = mode == "convergence_required" and _converged(receipt)
    if complete:
        receipt["stage"] = "converged"
        _write(root, receipt)
    observation = {
        "availability": "available",
        "boundary": {"status": "sealed", "proof_ref": "checkpoint=" + receipt["handoff_id"]},
        "source_session": {"status": "verified", "identity": payload["source"]["rollout"]["session_id"]},
        "capsule": {"status": "verified", "proof_ref": archive_uri},
        "archive": {"status": "verified", "proof_ref": archive_uri},
        "task": {"status": "completed" if complete else "incomplete", "completion_artifact": archive_uri + "/.done" if complete else None},
        "memory": {"status": "verified" if complete else "unverified", "proof_ref": archive_uri + "/memory_diff.json" if complete else None},
    }
    handoff.lifecycle_finalize_observation(root, handoff_path, observation, "openviking_checkpoint=" + receipt["handoff_id"])
    return receipt


def checkpoint(root: Path, handoff_path: str) -> dict[str, Any]:
    handoff_id, payload, _ = _prepared(root, handoff_path)
    events = handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)
    mode = handoff._prepared_mode(events)
    source_id, source_session = _source(payload)
    receipt = _load(root, handoff_id, source_id)
    marker = receipt["marker"]
    if not receipt["archive_uri"]:
        recovered = _archive_from_session(source_session, marker)
        if recovered:
            receipt.update({"archive_uri": recovered, "task_id": _task_for_archive(recovered), "stage": "archive_verified"})
            _write(root, receipt)
    if not receipt["archive_uri"]:
        if not _live_marker(source_session, marker):
            receipt["stage"] = "append_pending"
            _write(root, receipt)
            _ov("session", "add-message", source_session, "--role", "assistant", "--content", _envelope(handoff_id, payload), json_result=False)
        receipt["stage"] = "commit_pending"
        _write(root, receipt)
        response = _ov("session", "commit", source_session)
        archive_uri, task_id = _commit(response, source_session)
        receipt.update({"archive_uri": archive_uri, "task_id": task_id, "stage": "archive_verified"})
        _write(root, receipt)
    _verify_archive(receipt["archive_uri"], marker)
    if receipt["task_id"] is None:
        receipt["task_id"] = _task_for_archive(receipt["archive_uri"])
    if receipt["task_id"] is None:
        raise CheckpointError("OpenViking archive has no exact session-commit task")
    receipt["stage"] = "archive_verified"
    _write(root, receipt)
    receipt = _finalize(root, handoff_path, payload, receipt, mode)
    if mode == "archive_required" or receipt["stage"] == "converged":
        retired = handoff.ownership_operation(root, "retire-handoff", handoff_path, explicit=True)
        return {"status": "ready", "handoff_id": handoff_id, "stage": receipt["stage"], "archive_uri": receipt["archive_uri"], "task_id": receipt["task_id"], "ownership": retired["ownership"]}
    return {"status": "pending", "handoff_id": handoff_id, "stage": receipt["stage"], "archive_uri": receipt["archive_uri"], "task_id": receipt["task_id"]}


def status(root: Path, handoff_path: str) -> dict[str, Any]:
    # Status is a read-only receipt lookup.  After a successful checkpoint the
    # source ownership pointer is retired, so it must not rerun source fencing.
    handoff_id, _, payload = handoff._core(root, handoff_path)
    source_id, _ = _source(payload)
    receipt = _load(root, handoff_id, source_id)
    return {"status": "ready" if receipt["stage"] in {"archive_verified", "converged"} else "pending", **receipt}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("checkpoint", "status"):
        command = sub.add_parser(name)
        command.add_argument("--handoff", required=True)
    args = parser.parse_args()
    try:
        root = handoff._root(str(args.project_root))
        result = checkpoint(root, args.handoff) if args.command == "checkpoint" else status(root, args.handoff)
        print(json.dumps({"operation": args.command, **result}, ensure_ascii=True, sort_keys=True))
        return 0 if result["status"] == "ready" else 2
    except (CheckpointError, ContractError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"operation": args.command, "status": "recovery_required", "reason": str(exc)}, ensure_ascii=True, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
