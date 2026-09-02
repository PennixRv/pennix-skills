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
    r"(?:api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{20,})",
    re.IGNORECASE,
)


class ContractError(ValueError):
    """Raised when handoff input cannot be accepted safely."""


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
