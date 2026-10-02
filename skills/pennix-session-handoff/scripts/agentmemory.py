"""Minimal authenticated AgentMemory boundary for formal handoff writes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import quote, urlencode
from pathlib import Path
from typing import Any


PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class AgentMemoryError(RuntimeError):
    """Raised when the AgentMemory handoff contract cannot be proved."""


def _config_path() -> Path:
    raw = os.environ.get("AGENTMEMORY_CLIENT_CONFIG")
    return Path(raw).expanduser() if raw else Path.home() / ".config" / "agentmemory" / "client.env"


def _load_client_config() -> dict[str, str]:
    path = _config_path()
    if path.exists() and (path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077):
        raise AgentMemoryError("AgentMemory client config is missing or not private")
    values: dict[str, str] = {}
    if path.is_file():
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
        except (OSError, UnicodeError) as error:
            raise AgentMemoryError("AgentMemory client config is unreadable") from error
    values.update({key: value for key, value in os.environ.items() if key in {"AGENTMEMORY_URL", "AGENTMEMORY_SECRET", "AGENTMEMORY_PROJECT_NAME"} and value})
    return values


def _project_name(project_root: Path) -> str:
    canonical = project_root.resolve()
    registry = Path.home() / ".config" / "agentmemory" / "projects.json"
    mappings: dict[str, str] = {}
    if registry.exists():
        if registry.is_symlink() or not registry.is_file() or registry.stat().st_mode & 0o077:
            raise AgentMemoryError("AgentMemory project registry is not private")
        try:
            mappings = json.loads(registry.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AgentMemoryError("AgentMemory project registry is unreadable") from error
        if not isinstance(mappings, dict) or any(not isinstance(name, str) or not PROJECT_NAME.fullmatch(name) for name in mappings.values()):
            raise AgentMemoryError("AgentMemory project registry is invalid")
    value = _load_client_config().get("AGENTMEMORY_PROJECT_NAME") or mappings.get(str(canonical)) or canonical.name
    if not PROJECT_NAME.fullmatch(value):
        raise AgentMemoryError("AgentMemory project identity is invalid")
    return value


def handoff_content(handoff_id: str, capsule: str, key_fact: str) -> str:
    return f"Pennix formal handoff {handoff_id}.\nVerified key fact: {key_fact}\n\n{capsule}"


def _load_target(project_root: Path) -> tuple[str, str, str]:
    config = _load_client_config()
    api_url = config.get("AGENTMEMORY_URL")
    token = config.get("AGENTMEMORY_SECRET")
    if not isinstance(api_url, str) or not api_url.startswith(("http://", "https://")):
        raise AgentMemoryError("AgentMemory API URL is unavailable")
    if not isinstance(token, str) or not token.strip():
        raise AgentMemoryError("AgentMemory API secret is unavailable")
    return api_url.rstrip("/"), token, _project_name(project_root)


class AgentMemoryClient:
    def __init__(self, api_url: str, token: str, project: str, timeout: float = 15.0) -> None:
        self.base = api_url.rstrip("/")
        self.token = token
        self.project = project
        self.timeout = timeout

    @classmethod
    def for_project(cls, project_root: Path) -> "AgentMemoryClient":
        api_url, token, project = _load_target(project_root)
        return cls(api_url, token, project)

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
            raise AgentMemoryError(f"AgentMemory API request failed: {method} {path}") from error
        if not isinstance(value, dict):
            raise AgentMemoryError(f"AgentMemory API returned invalid JSON: {method} {path}")
        return value

    def _exact_memories(self, content: str, memory_id: str | None = None) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        # ponytail: bounded recovery over 500 records; use a native lookup key
        # if the upstream API later exposes one instead of an unbounded scan.
        for offset in range(0, 500, 100):
            query = urlencode({"project": self.project, "type": "workflow", "limit": 100, "offset": offset})
            page = self._request("GET", "/agentmemory/memories?" + query)
            records, total = page.get("memories"), page.get("total")
            if not isinstance(records, list) or not isinstance(total, int) or total < 0 or page.get("offset", offset) != offset:
                raise AgentMemoryError("AgentMemory recovery returned invalid pagination")
            matches.extend(item for item in records if isinstance(item, dict) and item.get("project") == self.project and item.get("type") == "workflow" and item.get("content") == content and (memory_id is None or item.get("id") == memory_id))
            if offset + len(records) >= total:
                return matches
            if len(records) != 100:
                raise AgentMemoryError("AgentMemory recovery returned an incomplete page")
        raise AgentMemoryError("AgentMemory exact recovery exceeds the bounded 500-record scan")

    def retain_handoff(self, handoff_id: str, capsule: str, key_fact: str, *, reconcile_only: bool = False) -> dict[str, Any]:
        digest = hashlib.sha256(capsule.encode("utf-8")).hexdigest()
        content = handoff_content(handoff_id, capsule, key_fact)
        try:
            if reconcile_only:
                raise AgentMemoryError("reconcile an interrupted write without repeating POST")
            response = self._request(
                "POST",
                "/agentmemory/remember",
                {
                    "content": content,
                    "type": "workflow",
                    "project": self.project,
                    "concepts": ["pennix", "session-handoff"],
                },
            )
        except AgentMemoryError:
            matches = self._exact_memories(content)
            if len(matches) != 1 or not isinstance(matches[0].get("id"), str):
                raise AgentMemoryError("AgentMemory handoff write outcome is ambiguous")
            return {"memory_id": matches[0]["id"], "content": content, "content_sha256": digest, "project": self.project}
        memory = response.get("memory")
        if response.get("success") is not True or not isinstance(memory, dict) or not isinstance(memory.get("id"), str):
            raise AgentMemoryError("AgentMemory handoff write did not return a memory id")
        return {"memory_id": memory["id"], "content": content, "content_sha256": digest, "project": self.project}

    def verify_retrieval(self, memory_id: str, content: str, handoff_id: str) -> int:
        try:
            value = self._request("GET", "/agentmemory/memories/" + quote(memory_id, safe=""))
            memory = value.get("memory")
        except AgentMemoryError:
            # ponytail: use the upstream bounded list when the 0.9.x by-id
            # route cannot read a record that the list route just indexed;
            # replace with a native idempotent read endpoint when upstream
            # exposes one consistently.
            matches = self._exact_memories(content, memory_id)
            if len(matches) != 1:
                raise AgentMemoryError("AgentMemory handoff retrieval was not uniquely proved")
            memory = matches[0]
        if not isinstance(memory, dict) or memory.get("id") != memory_id:
            raise AgentMemoryError("AgentMemory handoff retrieval returned the wrong memory")
        if memory.get("project") != self.project or memory.get("type") != "workflow" or memory.get("content") != content:
            raise AgentMemoryError("AgentMemory handoff retrieval did not prove the same project and content")
        if f"Pennix formal handoff {handoff_id}." not in content:
            raise AgentMemoryError("AgentMemory handoff identity is missing")
        return 1
