"""Small, stateless contracts shared by the project governance Skills."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple


MAX_REPORT_BYTES = 1024 * 1024
SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z0-9 ]+ PRIVATE KEY-----|"
    r"bearer\s+[A-Za-z0-9._~+/=-]{20,}|"
    r"(?:api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{20,})",
    re.IGNORECASE,
)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
REPORT_REQUIRED = {
    "schema_version", "result_id", "task_id", "batch_id", "role_id", "instance_id",
    "status", "scope", "evidence", "findings",
}
REPORT_OPTIONAL = {
    "observations", "uncertainties", "recommendations", "tool_summary",
    "error", "review_round", "review_of", "review_relation", "review_lens",
    "review_verdict", "evidence_refs", "coverage", "question", "content_digest",
}


class ContractError(ValueError):
    """Raised when a Skill input cannot be accepted safely."""


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


def load_json_file(path: Path, maximum_bytes: int = MAX_REPORT_BYTES) -> Dict[str, Any]:
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


def _validate_evidence(value: Any) -> Tuple[list[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    if not isinstance(value, list) or len(value) > 256:
        raise ContractError("evidence must be a list of at most 256 entries")
    entries: list[Dict[str, Any]] = []
    by_id: Dict[str, Dict[str, Any]] = {}
    for index, entry in enumerate(value):
        label = "evidence[%d]" % index
        if not isinstance(entry, dict) or set(entry) - {"id", "kind", "locator", "claim", "verified"}:
            raise ContractError("%s has unsupported fields" % label)
        for field in ("id", "kind", "locator", "claim"):
            if field not in entry:
                raise ContractError("%s.%s is required" % (label, field))
        evidence_id = _text(entry["id"], "%s.id" % label, 64)
        if not ID_RE.fullmatch(evidence_id) or evidence_id in by_id:
            raise ContractError("%s.id is invalid or duplicated" % label)
        if entry["kind"] not in {"file", "command", "url", "event"}:
            raise ContractError("%s.kind is invalid" % label)
        item = {
            "id": evidence_id,
            "kind": entry["kind"],
            "locator": _text(entry["locator"], "%s.locator" % label, 4096),
            "claim": _text(entry["claim"], "%s.claim" % label, 4096),
        }
        if "verified" in entry:
            if not isinstance(entry["verified"], bool):
                raise ContractError("%s.verified must be boolean" % label)
            item["verified"] = entry["verified"]
        entries.append(item)
        by_id[evidence_id] = item
    return entries, by_id


def validate_report(
    path: Path,
    expected_task: Optional[str] = None,
    expected_batch: Optional[str] = None,
    expected_instance: Optional[str] = None,
    expected_scope: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    payload = load_json_file(path)
    unknown = set(payload) - REPORT_REQUIRED - REPORT_OPTIONAL
    missing = REPORT_REQUIRED - set(payload)
    if unknown or missing:
        raise ContractError("report fields invalid; missing=%s unknown=%s" % (sorted(missing), sorted(unknown)))
    if payload.get("schema_version") != 2:
        raise ContractError("report schema_version must be 2")
    for field in ("result_id", "task_id", "batch_id", "role_id", "instance_id"):
        _text(payload[field], "report.%s" % field, 256)
    if expected_task is not None and payload["task_id"] != expected_task:
        raise ContractError("report task_id does not match the expected task")
    if expected_batch is not None and payload["batch_id"] != expected_batch:
        raise ContractError("report batch_id does not match the expected batch")
    if expected_instance is not None and payload["instance_id"] != expected_instance:
        raise ContractError("report instance_id does not match the expected instance")
    if payload["status"] not in {"complete", "incomplete", "blocked", "error"}:
        raise ContractError("report.status is invalid")
    scope = _text_list(payload["scope"], "report.scope", 64)
    if not scope:
        raise ContractError("report.scope must not be empty")
    if expected_scope is not None and scope != list(expected_scope):
        raise ContractError("report.scope must exactly preserve the assigned scope")
    evidence, by_id = _validate_evidence(payload["evidence"])
    if payload["status"] == "complete" and not evidence:
        raise ContractError("complete reports require at least one evidence entry")
    for field in ("observations", "uncertainties", "recommendations", "tool_summary"):
        if field in payload:
            _text_list(payload[field], "report.%s" % field, 256)
    findings = payload["findings"]
    if not isinstance(findings, list) or len(findings) > 128:
        raise ContractError("report.findings must be a list of at most 128 entries")
    for index, finding in enumerate(findings):
        label = "report.findings[%d]" % index
        if not isinstance(finding, dict) or set(finding) != {"severity", "claim", "impact", "reproduce", "evidence_ids"}:
            raise ContractError("%s fields are invalid" % label)
        if finding["severity"] not in {"critical", "major", "minor", "info"}:
            raise ContractError("%s.severity is invalid" % label)
        for field in ("claim", "impact", "reproduce"):
            _text(finding[field], "%s.%s" % (label, field), 8192)
        ids = _text_list(finding["evidence_ids"], "%s.evidence_ids" % label, 64)
        if any(evidence_id not in by_id for evidence_id in ids):
            raise ContractError("%s references unknown evidence" % label)
    if payload["status"] == "error" and "error" not in payload:
        raise ContractError("error reports require an error field")
    if "error" in payload:
        _text(payload["error"], "report.error", 8192)
    review_fields = {"review_round", "review_of", "review_relation", "review_lens", "review_verdict", "evidence_refs", "coverage"}
    review_present = review_fields.intersection(payload)
    if review_present and not review_fields.issubset(payload):
        raise ContractError("review metadata must be complete when present")
    if review_present:
        if not isinstance(payload["review_round"], int) or payload["review_round"] < 1:
            raise ContractError("review_round is invalid")
        review_of = _text_list(payload["review_of"], "review_of", 64)
        if not review_of or payload["review_relation"] not in {"independent", "supports", "refutes", "uncertain"}:
            raise ContractError("review relation is invalid")
        _text(payload["review_lens"], "review_lens", 256)
        if payload["review_verdict"] not in {"supports", "refutes", "uncertain"}:
            raise ContractError("review_verdict is invalid")
        refs = _text_list(payload["evidence_refs"], "evidence_refs", 64)
        if any(ref not in by_id for ref in refs):
            raise ContractError("review evidence_refs must reference this report")
        if payload["coverage"] not in {"complete", "partial", "blocked"}:
            raise ContractError("coverage is invalid")
    if "content_digest" in payload:
        given = payload["content_digest"]
        if not isinstance(given, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", given):
            raise ContractError("content_digest is invalid")
        without = dict(payload)
        del without["content_digest"]
        if given != digest(without):
            raise ContractError("content_digest does not match canonical report content")
    return payload


def report_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "result_id": payload["result_id"],
        "task_id": payload["task_id"],
        "batch_id": payload["batch_id"],
        "instance_id": payload["instance_id"],
        "status": payload["status"],
        "scope": payload["scope"],
        "finding_count": len(payload["findings"]),
    }
    if "review_verdict" in payload:
        summary["review_verdict"] = payload["review_verdict"]
    return summary
