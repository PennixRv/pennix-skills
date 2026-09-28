"""Minimal authenticated Hindsight API boundary for formal handoff writes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


PROJECT_BANK = re.compile(r"^pennix-project-[0-9a-f]{24}$")
TERMINAL = {"completed", "failed", "cancelled"}
HANDOFF_NAMESPACE = uuid.UUID("0c5bdf52-4b48-4ed1-ae25-1e3350f8e1c7")


class HindsightError(RuntimeError):
    """Raised when the Hindsight handoff contract cannot be proved."""


def _config_path() -> Path:
    raw = os.environ.get("HINDSIGHT_CONFIG")
    return Path(raw).expanduser() if raw else Path.home() / ".hindsight" / "coding-agent.json"


def _bank_id(project_root: Path, config: dict[str, Any]) -> str:
    config_path = project_root / ".trellis" / "config.yaml"
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as error:
        raise HindsightError("Trellis project memory identity is unavailable") from error
    matches = re.findall(r"(?m)^\s+bank_id:\s*['\"]?([^'\" #\r\n]+)", text)
    if len(matches) != 1 or not PROJECT_BANK.fullmatch(matches[0]):
        raise HindsightError("Trellis project memory identity is invalid")
    mappings = config.get("mapPathToBank")
    canonical = str(project_root.resolve())
    if not isinstance(mappings, dict) or mappings.get(canonical) != matches[0]:
        raise HindsightError("Hindsight project bank mapping is missing or mismatched")
    return matches[0]


def _load_target(project_root: Path) -> tuple[str, str, str]:
    path = _config_path()
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
        raise HindsightError("Hindsight native config is missing or not private")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HindsightError("Hindsight native config is unreadable") from error
    if not isinstance(config, dict):
        raise HindsightError("Hindsight native config is invalid")
    api_url = config.get("apiUrl")
    token = config.get("apiToken")
    if not isinstance(api_url, str) or not api_url.startswith(("http://", "https://")):
        raise HindsightError("Hindsight API URL is unavailable")
    if not isinstance(token, str) or not token.strip():
        raise HindsightError("Hindsight API token is unavailable")
    return api_url.rstrip("/"), token, _bank_id(project_root, config)


class HindsightClient:
    def __init__(self, api_url: str, token: str, bank_id: str, timeout: float = 15.0) -> None:
        self.base = f"{api_url}/v1/default/banks/{bank_id}"
        self.token = token
        self.bank_id = bank_id
        self.timeout = timeout

    @classmethod
    def for_project(cls, project_root: Path) -> "HindsightClient":
        api_url, token, bank_id = _load_target(project_root)
        return cls(api_url, token, bank_id)

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            self.base + path,
            data=encoded,
            method=method,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer " + self.token,
                **({"Content-Type": "application/json"} if encoded is not None else {}),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                value = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as error:
            raise HindsightError(f"Hindsight API request failed: {method} {path}") from error
        if not isinstance(value, dict):
            raise HindsightError(f"Hindsight API returned invalid JSON: {method} {path}")
        return value

    def retain_handoff(self, handoff_id: str, capsule: str, key_fact: str) -> dict[str, Any]:
        digest = hashlib.sha256(capsule.encode("utf-8")).hexdigest()
        document_id = "pennix-handoff-" + handoff_id
        operation_id = str(uuid.uuid5(HANDOFF_NAMESPACE, handoff_id))
        response = self._request(
            "POST",
            "/memories",
            {
                "items": [
                    {
                        "content": f"Pennix formal handoff {handoff_id}.\nVerified key fact: {key_fact}\n\n{capsule}",
                        "context": "Pennix formal session handoff",
                        "document_id": document_id,
                        "tags": ["source:pennix", "scope:handoff"],
                        "metadata": {"handoff_id": handoff_id, "content_sha256": digest},
                        "strategy": "conversation",
                        "update_mode": "replace",
                    }
                ],
                "async": True,
                "operation_id": operation_id,
            },
        )
        returned = response.get("operation_id")
        if returned != operation_id:
            raise HindsightError("Hindsight retain did not return the expected operation id")
        return {"document_id": document_id, "operation_id": operation_id, "content_sha256": digest}

    def wait_operation(self, operation_id: str, timeout_seconds: float = 60.0) -> str:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            value = self._request("GET", "/operations/" + operation_id)
            status = value.get("status")
            if isinstance(status, str) and status.lower() in TERMINAL:
                status = status.lower()
                if status != "completed":
                    raise HindsightError("Hindsight handoff operation failed")
                return status
            time.sleep(1)
        raise HindsightError("Hindsight handoff operation timed out")

    def verify_retrieval(self, document_id: str, handoff_id: str) -> int:
        value = self._request(
            "POST",
            "/memories/recall",
            {"query": handoff_id, "types": ["world", "experience", "observation"], "max_tokens": 2000, "budget": "low"},
        )
        results = value.get("results")
        if not isinstance(results, list):
            raise HindsightError("Hindsight retrieval response is invalid")
        matches = [
            item
            for item in results
            if isinstance(item, dict)
            and item.get("document_id") == document_id
            and isinstance(item.get("text"), str)
            and item["text"].strip()
            and isinstance(item.get("metadata"), dict)
            and item["metadata"].get("handoff_id") == handoff_id
        ]
        if not matches:
            raise HindsightError("Hindsight handoff retrieval did not prove the same document")
        return len(matches)


def complete_handoff(project_root: Path, handoff_id: str, capsule: str, key_fact: str) -> dict[str, Any]:
    client = HindsightClient.for_project(project_root)
    result = client.retain_handoff(handoff_id, capsule, key_fact)
    result["operation_status"] = client.wait_operation(result["operation_id"])
    result["retrieval_count"] = client.verify_retrieval(result["document_id"], handoff_id)
    result["bank_id"] = client.bank_id
    return result
