"""Small local contracts used by the independently installable request builder."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict


SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z0-9 ]+ PRIVATE KEY-----|"
    r"bearer\s+[A-Za-z0-9._~+/=-]{20,}|"
    r"(?:api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{20,})",
    re.IGNORECASE,
)


class ContractError(ValueError):
    """Raised when a candidate request cannot be accepted safely."""


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


def normalize_candidate_request(value: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {
        "question",
        "scope",
        "lens",
        "role_id",
        "evidence_method",
        "review_policy",
    }
    unknown = set(value) - allowed
    if unknown:
        raise ContractError("request has unknown fields: %s" % sorted(unknown))
    result = {
        "schema_version": 1,
        "question": _text(value.get("question"), "question", 8192),
        "scope": _text_list(value.get("scope"), "scope", 64),
        "lens": _text(value.get("lens"), "lens", 256),
        "role_id": _text(value.get("role_id"), "role_id", 128),
        "evidence_method": _text(value.get("evidence_method"), "evidence_method", 2048),
    }
    if not result["scope"]:
        raise ContractError("scope must not be empty")
    policy = value.get("review_policy")
    if policy is not None:
        if not isinstance(policy, dict) or set(policy) != {"mode", "risk", "reason"}:
            raise ContractError("review_policy fields are invalid")
        if policy["mode"] not in {"required", "exempt"} or policy["risk"] not in {
            "low",
            "major",
            "critical",
        }:
            raise ContractError("review_policy mode or risk is invalid")
        if policy["mode"] == "exempt" and policy["risk"] != "low":
            raise ContractError("only low-risk requests may exempt review")
        result["review_policy"] = {
            "mode": policy["mode"],
            "risk": policy["risk"],
            "reason": _text(policy["reason"], "review_policy.reason", 2048),
        }
    return result


def write_output(path: Path, content: str) -> None:
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise ContractError("output must be a regular file")
    for parent in (path.parent, *path.parent.parents):
        if parent.is_symlink():
            raise ContractError("output parent must not contain a symbolic path")
        if parent == Path(parent.anchor) or parent == Path("."):
            break
    if path.parent.exists() and not path.parent.is_dir():
        raise ContractError("output parent must be a regular directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    descriptor, temporary_name = tempfile.mkstemp(prefix=".%s." % path.name, dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
