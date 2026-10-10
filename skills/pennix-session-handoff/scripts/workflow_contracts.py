"""Small local contracts used by the independently installable handoff Skill."""

from __future__ import annotations

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


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TARGET_SOURCE_RE = re.compile(r"^session:[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
LIFECYCLE_MODES = {"core_only"}
OBSERVATION_AVAILABILITY = {"available", "unsupported", "unavailable"}
BOUNDARY_STATUSES = {"sealed", "unsealed"}
PROOF_STATUSES = {"verified", "unverified"}
TASK_STATUSES = {"completed", "incomplete", "unknown"}


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("%s must be a non-empty string" % label)
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ContractError("%s contains control characters" % label)
    return value


def free_text(value: Any, label: str) -> str:
    """Validate semantic prose without imposing a workflow length limit."""
    if not isinstance(value, str):
        raise ContractError("%s must be a string" % label)
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ContractError("%s contains control characters" % label)
    return value


def _text_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ContractError("%s must be a list of strings" % label)
    return [_text(item, "%s[%d]" % (label, index)) for index, item in enumerate(value)]


def _fields(value: Any, fields: set[str], label: str) -> Dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ContractError("%s fields are invalid" % label)
    return value


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ContractError("%s must be an integer >= %d" % (label, minimum))
    return value


def load_json_file(path: Path) -> Dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ContractError("JSON input must be a regular file: %s" % path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("JSON input is unreadable or invalid") from exc
    if not isinstance(value, dict):
        raise ContractError("JSON input must be an object")
    if SECRET_RE.search(json.dumps(value, ensure_ascii=False)):
        raise ContractError("JSON input contains a possible credential or secret")
    return value


def safe_id(value: Any, label: str) -> str:
    result = _text(value, label)
    if not SAFE_ID_RE.fullmatch(result):
        raise ContractError("%s is unsafe" % label)
    return result


def lifecycle_mode(value: Any) -> str:
    result = _text(value, "mode")
    if result not in LIFECYCLE_MODES:
        raise ContractError("mode is unsupported")
    return result


def validate_observation(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "availability", "boundary", "source_session", "capsule", "task", "memory"
    }:
        raise ContractError("observation fields are invalid")
    availability = _text(value["availability"], "observation.availability")
    if availability not in OBSERVATION_AVAILABILITY:
        raise ContractError("observation availability is invalid")

    boundary = value["boundary"]
    if not isinstance(boundary, dict) or set(boundary) != {"status", "proof_ref"}:
        raise ContractError("observation boundary is invalid")
    boundary_status = _text(boundary["status"], "observation.boundary.status")
    if boundary_status not in BOUNDARY_STATUSES:
        raise ContractError("observation boundary status is invalid")
    boundary_proof_ref = boundary["proof_ref"]
    if boundary_proof_ref is not None:
        _text(boundary_proof_ref, "observation.boundary.proof_ref")

    source_session = value["source_session"]
    if not isinstance(source_session, dict) or set(source_session) != {"status", "identity"}:
        raise ContractError("observation source session is invalid")
    source_status = _text(source_session["status"], "observation.source_session.status")
    if source_status not in PROOF_STATUSES:
        raise ContractError("observation source session status is invalid")
    if source_session["identity"] is not None:
        _text(source_session["identity"], "observation.source_session.identity")

    proofs: Dict[str, Any] = {}
    for name in ("capsule",):
        item = value[name]
        if not isinstance(item, dict) or set(item) not in ({"status", "proof_ref"}, {"status", "exact_read_digest"}):
            raise ContractError("observation.%s is invalid" % name)
        status = _text(item["status"], "observation.%s.status" % name)
        if status not in PROOF_STATUSES:
            raise ContractError("observation.%s status is invalid" % name)
        proof_ref = item.get("proof_ref", item.get("exact_read_digest"))
        if proof_ref is not None:
            _text(proof_ref, "observation.%s.proof_ref" % name)
        proofs[name] = {"status": status, "proof_ref": proof_ref}

    task = value["task"]
    if not isinstance(task, dict) or set(task) != {"status", "completion_artifact"}:
        raise ContractError("observation task is invalid")
    task_status = _text(task["status"], "observation.task.status")
    if task_status not in TASK_STATUSES:
        raise ContractError("observation task status is invalid")
    if task["completion_artifact"] is not None:
        _text(task["completion_artifact"], "observation.task.completion_artifact")

    memory = value["memory"]
    if not isinstance(memory, dict) or set(memory) not in ({"status", "proof_ref"}, {"status", "diff_digest"}):
        raise ContractError("observation memory is invalid")
    memory_status = _text(memory["status"], "observation.memory.status")
    if memory_status not in PROOF_STATUSES:
        raise ContractError("observation memory status is invalid")
    memory_proof_ref = memory.get("proof_ref", memory.get("diff_digest"))
    if memory_proof_ref is not None:
        _text(memory_proof_ref, "observation.memory.proof_ref")

    normalized = {
        "availability": availability,
        "boundary": {"status": boundary_status, "proof_ref": boundary_proof_ref},
        "source_session": {"status": source_status, "identity": source_session["identity"]},
        "capsule": proofs["capsule"],
        "task": {"status": task_status, "completion_artifact": task["completion_artifact"]},
        "memory": {"status": memory_status, "proof_ref": memory_proof_ref},
    }
    if SECRET_RE.search(json.dumps(normalized, ensure_ascii=False)):
        raise ContractError("observation contains a possible credential or secret")
    return normalized


def validate_attestation(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "target_source", "core_view_read", "prompt_read", "trellis_started", "facts_reconciled",
        "action_authorized", "task_disposition", "task_path", "continuation_status",
        "history_read", "history_refs"
    }:
        raise ContractError("attestation fields are invalid")
    target_source = _text(value["target_source"], "attestation.target_source")
    if not TARGET_SOURCE_RE.fullmatch(target_source):
        raise ContractError("attestation target source is not a direct session source")
    for field in ("core_view_read", "prompt_read", "trellis_started", "facts_reconciled", "action_authorized"):
        if not isinstance(value[field], bool):
            raise ContractError("attestation.%s is invalid" % field)
    if value["action_authorized"]:
        raise ContractError("initial admission cannot authorize pending action")
    history_read = _text(value["history_read"], "attestation.history_read")
    history_refs = value["history_refs"]
    if history_read not in {"none", "partial", "full"} or not isinstance(history_refs, list):
        raise ContractError("attestation history reading is invalid")
    if (history_read == "none") != (not history_refs):
        raise ContractError("attestation history scope and references disagree")
    for reference in history_refs:
        _fields(reference, {"event_index", "offset", "next_offset"}, "history reference")
        if reference["event_index"] is not None:
            _integer(reference["event_index"], "history reference event_index", 1)
        offset = _integer(reference["offset"], "history reference offset")
        _integer(reference["next_offset"], "history reference next_offset", offset + 1)
    disposition = _text(value["task_disposition"], "attestation.task_disposition")
    if disposition not in {"incomplete", "complete", "blocked", "none"}:
        raise ContractError("attestation task disposition is invalid")
    task_path = value["task_path"]
    if task_path is not None:
        task_path = _text(task_path, "attestation.task_path")
        candidate = Path(task_path)
        if candidate.is_absolute() or ".." in candidate.parts or not task_path.startswith(".trellis/tasks/"):
            raise ContractError("attestation task path is unsafe")
    continuation = value["continuation_status"]
    if continuation is not None:
        continuation = _text(continuation, "attestation.continuation_status")
        if continuation not in {"absent", "ready", "stale", "withheld"}:
            raise ContractError("attestation continuation status is invalid")
    normalized = {
        "target_source": target_source, "core_view_read": value["core_view_read"], "prompt_read": value["prompt_read"],
        "trellis_started": value["trellis_started"], "facts_reconciled": value["facts_reconciled"],
        "action_authorized": False, "task_disposition": disposition,
        "task_path": task_path, "continuation_status": continuation,
        "history_read": history_read, "history_refs": history_refs,
    }
    if SECRET_RE.search(json.dumps(normalized, ensure_ascii=False)):
        raise ContractError("attestation contains a possible credential or secret")
    return normalized
