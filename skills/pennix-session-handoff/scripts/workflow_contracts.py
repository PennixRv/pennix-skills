"""Small local contracts used by the independently installable handoff Skill."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict


SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z0-9 ]+ PRIVATE KEY-----|"
    r"bearer\s+[A-Za-z0-9._~+/=-]{20,}|"
    r"\b(?:sk|th)-[A-Za-z0-9_-]{20,}|"
    r"(?:api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{20,})",
    re.IGNORECASE,
)


class ContractError(ValueError):
    """Raised when handoff input cannot be accepted safely."""


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TARGET_SOURCE_RE = re.compile(r"^session:[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
LIFECYCLE_MODES = {"core_only", "capsule_required", "archive_required", "convergence_required"}
OBSERVATION_AVAILABILITY = {"available", "unsupported", "unavailable"}
BOUNDARY_STATUSES = {"sealed", "unsealed"}
PROOF_STATUSES = {"verified", "unverified"}
TASK_STATUSES = {"completed", "incomplete", "unknown"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def _text(value: Any, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ContractError("%s must be a non-empty string" % label)
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ContractError("%s contains control characters" % label)
    return value


def _text_list(value: Any, label: str, maximum: int = 64) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ContractError("%s must be a list of at most %d strings" % (label, maximum))
    result = [_text(item, "%s[%d]" % (label, index), 4096) for index, item in enumerate(value)]
    if len(set(result)) != len(result):
        raise ContractError("%s must not contain duplicates" % label)
    return result


def load_json_file(path: Path, maximum_bytes: int = 64 * 1024) -> Dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ContractError("JSON input must be a regular file: %s" % path)
    if path.stat().st_size > maximum_bytes:
        raise ContractError("JSON input exceeds %d bytes" % maximum_bytes)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("JSON input is unreadable or invalid") from exc
    if not isinstance(value, dict):
        raise ContractError("JSON input must be an object")
    if SECRET_RE.search(json.dumps(value, ensure_ascii=False)):
        raise ContractError("JSON input contains a possible credential or secret")
    return value


def bounded_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ContractError("%s is invalid" % label)
    return value


def safe_id(value: Any, label: str) -> str:
    result = _text(value, label, 128)
    if not SAFE_ID_RE.fullmatch(result):
        raise ContractError("%s is unsafe" % label)
    return result


def lifecycle_mode(value: Any) -> str:
    result = _text(value, "mode", 32)
    if result not in LIFECYCLE_MODES:
        raise ContractError("mode is unsupported")
    return result


def validate_observation(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "availability", "boundary", "source_session", "capsule", "archive", "task", "memory"
    }:
        raise ContractError("observation fields are invalid")
    availability = _text(value["availability"], "observation.availability", 16)
    if availability not in OBSERVATION_AVAILABILITY:
        raise ContractError("observation availability is invalid")

    boundary = value["boundary"]
    if not isinstance(boundary, dict) or set(boundary) != {"status", "proof_ref"}:
        raise ContractError("observation boundary is invalid")
    boundary_status = _text(boundary["status"], "observation.boundary.status", 16)
    if boundary_status not in BOUNDARY_STATUSES:
        raise ContractError("observation boundary status is invalid")
    proof_ref = boundary["proof_ref"]
    if proof_ref is not None:
        _text(proof_ref, "observation.boundary.proof_ref", 512)

    source_session = value["source_session"]
    if not isinstance(source_session, dict) or set(source_session) != {"status", "identity"}:
        raise ContractError("observation source session is invalid")
    source_status = _text(source_session["status"], "observation.source_session.status", 16)
    if source_status not in PROOF_STATUSES:
        raise ContractError("observation source session status is invalid")
    if source_session["identity"] is not None:
        _text(source_session["identity"], "observation.source_session.identity", 256)

    proofs: Dict[str, Any] = {}
    for name in ("capsule", "archive"):
        item = value[name]
        if not isinstance(item, dict) or set(item) != {"status", "exact_read_digest"}:
            raise ContractError("observation.%s is invalid" % name)
        status = _text(item["status"], "observation.%s.status" % name, 16)
        if status not in PROOF_STATUSES:
            raise ContractError("observation.%s status is invalid" % name)
        digest_value = item["exact_read_digest"]
        if digest_value is not None:
            bounded_digest(digest_value, "observation.%s.exact_read_digest" % name)
        proofs[name] = {"status": status, "exact_read_digest": digest_value}

    task = value["task"]
    if not isinstance(task, dict) or set(task) != {"status", "completion_artifact"}:
        raise ContractError("observation task is invalid")
    task_status = _text(task["status"], "observation.task.status", 16)
    if task_status not in TASK_STATUSES:
        raise ContractError("observation task status is invalid")
    if task["completion_artifact"] is not None:
        _text(task["completion_artifact"], "observation.task.completion_artifact", 1024)

    memory = value["memory"]
    if not isinstance(memory, dict) or set(memory) != {"status", "diff_digest"}:
        raise ContractError("observation memory is invalid")
    memory_status = _text(memory["status"], "observation.memory.status", 16)
    if memory_status not in PROOF_STATUSES:
        raise ContractError("observation memory status is invalid")
    if memory["diff_digest"] is not None:
        bounded_digest(memory["diff_digest"], "observation.memory.diff_digest")

    normalized = {
        "availability": availability,
        "boundary": {"status": boundary_status, "proof_ref": proof_ref},
        "source_session": {"status": source_status, "identity": source_session["identity"]},
        "capsule": proofs["capsule"], "archive": proofs["archive"],
        "task": {"status": task_status, "completion_artifact": task["completion_artifact"]},
        "memory": {"status": memory_status, "diff_digest": memory["diff_digest"]},
    }
    if SECRET_RE.search(json.dumps(normalized, ensure_ascii=False)):
        raise ContractError("observation contains a possible credential or secret")
    return normalized


def validate_attestation(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "target_source", "prompt_read", "trellis_started", "facts_reconciled",
        "action_authorized", "task_disposition", "task_path", "continuation_status"
    }:
        raise ContractError("attestation fields are invalid")
    target_source = _text(value["target_source"], "attestation.target_source", 192)
    if not TARGET_SOURCE_RE.fullmatch(target_source):
        raise ContractError("attestation target source is not a direct session source")
    for field in ("prompt_read", "trellis_started", "facts_reconciled", "action_authorized"):
        if not isinstance(value[field], bool):
            raise ContractError("attestation.%s is invalid" % field)
    if value["action_authorized"]:
        raise ContractError("initial admission cannot authorize pending action")
    disposition = _text(value["task_disposition"], "attestation.task_disposition", 16)
    if disposition not in {"incomplete", "complete", "blocked", "none"}:
        raise ContractError("attestation task disposition is invalid")
    task_path = value["task_path"]
    if task_path is not None:
        task_path = _text(task_path, "attestation.task_path", 1024)
        candidate = Path(task_path)
        if candidate.is_absolute() or ".." in candidate.parts or not task_path.startswith(".trellis/tasks/"):
            raise ContractError("attestation task path is unsafe")
    continuation = value["continuation_status"]
    if continuation is not None:
        continuation = _text(continuation, "attestation.continuation_status", 16)
        if continuation not in {"absent", "ready", "stale", "withheld"}:
            raise ContractError("attestation continuation status is invalid")
    normalized = {
        "target_source": target_source, "prompt_read": value["prompt_read"],
        "trellis_started": value["trellis_started"], "facts_reconciled": value["facts_reconciled"],
        "action_authorized": False, "task_disposition": disposition,
        "task_path": task_path, "continuation_status": continuation,
    }
    if SECRET_RE.search(json.dumps(normalized, ensure_ascii=False)):
        raise ContractError("attestation contains a possible credential or secret")
    return normalized
