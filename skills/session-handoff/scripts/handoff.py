#!/usr/bin/env python3
"""Minimal, explicit-user-request-only Trellis session handoff helper."""

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
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import ContractError, SECRET_RE, _text, _text_list, canonical, digest, load_json_file  # noqa: E402


HANDOFF = ".trellis/session-handoff.json"
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
AUTHORIZATION = {
    "source": "current_user_explicit_request",
    "attestation": "coordinator_asserted_not_runtime_verified",
}


def _root(value: str) -> Path:
    root = Path(value).resolve()
    trellis = root / ".trellis"
    if not root.is_dir() or trellis.is_symlink() or not trellis.is_dir():
        raise ContractError("project root must contain .trellis")
    return root


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


def _task_snapshot(root: Path) -> Optional[Dict[str, str]]:
    script = root / ".trellis/scripts/task.py"
    if script.is_symlink() or not script.is_file():
        raise ContractError("task.py is missing or unsafe")
    result = subprocess.run(
        [sys.executable, str(script), "current", "--json"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
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
    task_path = Path(str(selected.get("dir", "")))
    if task_path.is_absolute() or ".." in task_path.parts or not str(task_path).startswith(".trellis/tasks/"):
        raise ContractError("active task path is unsafe")
    task_candidate = _project_file(root, task_path.as_posix(), "active task path")
    if not task_candidate.is_dir():
        raise ContractError("active task directory is unavailable")
    task_dir = task_candidate
    files: List[tuple[str, str]] = []
    for path in sorted(task_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        files.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    return {
        "id": _text(selected.get("id"), "task.id", 256),
        "path": task_path.as_posix(),
        "status": _text(selected.get("status"), "task.status", 64),
        "material_digest": digest(files),
    }


def _git_snapshot(root: Path) -> Dict[str, Any]:
    def run(*args: str) -> str:
        result = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            raise ContractError("git snapshot failed")
        return result.stdout.decode("utf-8", errors="strict").strip()

    branch = run("branch", "--show-current") or None
    head = run("rev-parse", "HEAD") or None
    dirty_lines = [line for line in run("status", "--porcelain=v1").splitlines() if HANDOFF not in line]
    dirty = "\n".join(dirty_lines)
    return {
        "branch": branch,
        "head": head,
        "worktree_state": "dirty" if dirty else "clean",
        "dirty_paths_digest": digest(dirty.splitlines()),
        "scope": {"mode": "full", "paths": []},
    }


def _source(root: Path, task: Optional[Dict[str, str]]) -> Dict[str, Any]:
    git = _git_snapshot(root)
    return {
        "task": task,
        "git": git,
        "digest": digest({"task": task, "git": git}),
    }


def _payload_digest(payload: Dict[str, Any]) -> str:
    return digest({key: value for key, value in payload.items() if key != "integrity"})


def _digest_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_DIGEST.fullmatch(value):
        raise ContractError("%s is invalid" % label)
    return value


def _validate_payload_shape(root: Path, payload: Dict[str, Any]) -> None:
    expected = {
        "schema_version", "kind", "created_at", "project", "work_context", "source",
        "verified", "pending", "governance", "memory_projection", "authorization", "integrity",
    }
    if set(payload) != expected:
        raise ContractError("handoff fields are invalid")
    if payload["schema_version"] != 3 or payload["kind"] != "trellis-session-handoff":
        raise ContractError("handoff schema is unsupported")
    _text(payload["created_at"], "created_at", 128)

    project = payload["project"]
    if not isinstance(project, dict) or set(project) != {"name", "identity_digest"}:
        raise ContractError("handoff project is invalid")
    if _text(project["name"], "project.name", 256) != root.name:
        raise ContractError("handoff project does not match the current root")
    if project["identity_digest"] != digest({"name": root.name, "marker": ".trellis"}):
        raise ContractError("handoff project identity is invalid")

    context = payload["work_context"]
    if not isinstance(context, dict) or set(context) != {"task"}:
        raise ContractError("handoff work context is invalid")
    task = context["task"]
    if task is not None:
        if not isinstance(task, dict) or set(task) != {"id", "path", "status", "material_digest"}:
            raise ContractError("handoff task is invalid")
        _text(task["id"], "task.id", 256)
        task_path = _text(task["path"], "task.path", 1024)
        if not task_path.startswith(".trellis/tasks/") or "/archive/" in task_path:
            raise ContractError("handoff task path is invalid")
        _digest_text(task["material_digest"], "task.material_digest")
        _text(task["status"], "task.status", 64)

    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"session_label", "git", "evidence_digest"}:
        raise ContractError("handoff source is invalid")
    _text(source["session_label"], "source.session_label", 128)
    _digest_text(source["evidence_digest"], "source.evidence_digest")
    git = source["git"]
    if not isinstance(git, dict) or set(git) != {"branch", "head", "worktree_state", "dirty_paths_digest", "scope"}:
        raise ContractError("handoff source git is invalid")
    for field in ("branch", "head"):
        if git[field] is not None:
            _text(git[field], "source.git.%s" % field, 256)
    if git["worktree_state"] not in {"clean", "dirty"}:
        raise ContractError("handoff source git state is invalid")
    _digest_text(git["dirty_paths_digest"], "source.git.dirty_paths_digest")
    if git["scope"] != {"mode": "full", "paths": []}:
        raise ContractError("handoff source git scope is invalid")

    verified = payload["verified"]
    if not isinstance(verified, dict) or set(verified) != {"facts", "evidence_paths", "validation"}:
        raise ContractError("handoff verified context is invalid")
    evidence_paths = _text_list(verified["evidence_paths"], "verified.evidence_paths", 32)
    for relative in evidence_paths:
        target = _project_file(root, relative, "evidence path")
        if not target.is_file():
            raise ContractError("evidence path is missing or unsafe: %s" % relative)
    if source["evidence_digest"] != digest(evidence_paths):
        raise ContractError("handoff evidence digest does not match")
    _text_list(verified["facts"], "verified.facts", 24)
    validation = verified["validation"]
    if not isinstance(validation, list) or len(validation) > 16:
        raise ContractError("verified.validation must be a list of at most 16 entries")
    for index, item in enumerate(validation):
        if not isinstance(item, dict) or set(item) != {"command", "result"}:
            raise ContractError("verified.validation[%d] fields are invalid" % index)
        _text(item["command"], "verified.validation[%d].command" % index, 512)
        _text(item["result"], "verified.validation[%d].result" % index, 512)

    pending = payload["pending"]
    if not isinstance(pending, dict) or set(pending) != {"next_action", "blockers", "risks"}:
        raise ContractError("handoff pending context is invalid")
    _text(pending["next_action"], "pending.next_action", 512)
    _text_list(pending["blockers"], "pending.blockers", 16)
    _text_list(pending["risks"], "pending.risks", 16)

    if payload["governance"] != {"mode": "none", "batch": None}:
        raise ContractError("handoff governance is invalid")
    memory = payload["memory_projection"]
    if not isinstance(memory, dict) or set(memory) != {"local", "archive_refs", "openviking"}:
        raise ContractError("handoff memory projection is invalid")
    for field in ("local", "archive_refs", "openviking"):
        _text_list(memory[field], "memory_projection.%s" % field, 32)
    if payload["authorization"] != AUTHORIZATION:
        raise ContractError("handoff authorization is invalid")
    integrity = payload["integrity"]
    if not isinstance(integrity, dict) or set(integrity) != {"payload_digest", "source_digest"}:
        raise ContractError("handoff integrity is invalid")
    _digest_text(integrity["payload_digest"], "integrity.payload_digest")
    _digest_text(integrity["source_digest"], "integrity.source_digest")


def _request(root: Path, path: Path) -> Dict[str, Any]:
    value = load_json_file(path, 64 * 1024)
    required = {"session_label", "facts", "evidence_paths", "next_action", "blockers", "risks", "validation"}
    if set(value) != required:
        raise ContractError("handoff request fields are invalid")
    evidence_paths = _text_list(value["evidence_paths"], "evidence_paths", 32)
    for relative in evidence_paths:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts or str(candidate).startswith(".trellis/.runtime/"):
            raise ContractError("evidence_paths must be project-relative non-runtime paths")
        target = _project_file(root, relative, "evidence path")
        if not target.is_file():
            raise ContractError("evidence path is missing or unsafe: %s" % relative)
    validation = value["validation"]
    if not isinstance(validation, list) or len(validation) > 16:
        raise ContractError("validation must be a list of at most 16 entries")
    normalized_validation = []
    for index, item in enumerate(validation):
        if not isinstance(item, dict) or set(item) != {"command", "result"}:
            raise ContractError("validation[%d] fields are invalid" % index)
        normalized_validation.append({
            "command": _text(item["command"], "validation[%d].command" % index, 512),
            "result": _text(item["result"], "validation[%d].result" % index, 512),
        })
    normalized = {
        "session_label": _text(value["session_label"], "session_label", 128),
        "facts": _text_list(value["facts"], "facts", 24),
        "evidence_paths": evidence_paths,
        "next_action": _text(value["next_action"], "next_action", 512),
        "blockers": _text_list(value["blockers"], "blockers", 16),
        "risks": _text_list(value["risks"], "risks", 16),
        "validation": normalized_validation,
    }
    if SECRET_RE.search(json.dumps(normalized, ensure_ascii=False)):
        raise ContractError("handoff request contains a possible credential or secret")
    return normalized


def build(root: Path, request: Dict[str, Any]) -> Dict[str, Any]:
    task = _task_snapshot(root)
    source = _source(root, task)
    payload: Dict[str, Any] = {
        "schema_version": 3,
        "kind": "trellis-session-handoff",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project": {"name": root.name, "identity_digest": digest({"name": root.name, "marker": ".trellis"})},
        "work_context": {"task": task},
        "source": {"session_label": request["session_label"], "git": source["git"], "evidence_digest": digest(request["evidence_paths"])},
        "verified": {"facts": request["facts"], "evidence_paths": request["evidence_paths"], "validation": request["validation"]},
        "pending": {"next_action": request["next_action"], "blockers": request["blockers"], "risks": request["risks"]},
        "governance": {"mode": "none", "batch": None},
        "memory_projection": {"local": [], "archive_refs": [], "openviking": []},
        "authorization": dict(AUTHORIZATION),
    }
    payload["integrity"] = {"payload_digest": _payload_digest(payload), "source_digest": source["digest"]}
    return payload


def validate(root: Path, payload: Dict[str, Any]) -> str:
    _validate_payload_shape(root, payload)
    integrity = payload["integrity"]
    if integrity["payload_digest"] != _payload_digest(payload):
        raise ContractError("handoff payload digest does not match")
    current = _source(root, _task_snapshot(root))
    recorded = payload["source"]
    if recorded["git"] != current["git"]:
        return "changed"
    if integrity["source_digest"] != current["digest"]:
        return "changed"
    return "ready"


def emit(operation: str, status: str, reason: Optional[str] = None) -> None:
    result: Dict[str, Any] = {"operation": operation, "status": status}
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
    sub.add_parser("validate")
    args = parser.parse_args()
    try:
        root = _root(str(args.project_root))
        destination = root / HANDOFF
        if args.command == "validate":
            if not destination.exists():
                emit("validate", "absent")
                return 0
            if destination.is_symlink() or not destination.is_file():
                emit("validate", "recovery_required", "handoff path is unsafe")
                return 2
            status = validate(root, load_json_file(destination, 64 * 1024))
            emit("validate", status)
            return 0 if status == "ready" else 2
        if not args.explicit_user_request:
            raise ContractError("write requires --explicit-user-request")
        request = _request(root, args.request)
        payload = build(root, request)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, destination)
        emit("write", "ready")
        return 0
    except (ContractError, OSError, subprocess.SubprocessError) as exc:
        emit(getattr(args, "command", "handoff"), "recovery_required", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
