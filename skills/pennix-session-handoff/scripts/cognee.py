"""Minimal authenticated Cognee boundary for formal handoff writes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CONFIG_PATH = Path(".cognee") / ".env"
REGISTRY_PATH = Path(".config") / "cognee" / "projects.json"


class CogneeError(RuntimeError):
    """Raised when the Cognee handoff contract cannot be proved."""


def _config_path() -> Path:
    raw = os.environ.get("COGNEE_CONFIG")
    return Path(raw).expanduser() if raw else Path.home() / CONFIG_PATH


def _load_env(path: Path) -> dict[str, str]:
    if path.exists() and (path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077):
        raise CogneeError("Cognee client config is missing or not private")
    values: dict[str, str] = {}
    if path.is_file():
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.removeprefix("export ").split("=", 1)
                values[key.strip()] = value.strip().strip('"\'')
        except (OSError, UnicodeError) as error:
            raise CogneeError("Cognee client config is unreadable") from error
    values.update({key: value for key, value in os.environ.items() if key in {"COGNEE_BASE_URL", "COGNEE_API_KEY", "COGNEE_PROJECT_NAME", "COGNEE_DATASET_ID"} and value})
    return values


def _project_name(project_root: Path) -> str:
    canonical = project_root.resolve()
    registry = Path.home() / REGISTRY_PATH
    mappings: dict[str, Any] = {}
    if registry.exists():
        if registry.is_symlink() or not registry.is_file() or registry.stat().st_mode & 0o077:
            raise CogneeError("Cognee project registry is not private")
        try:
            mappings = json.loads(registry.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CogneeError("Cognee project registry is unreadable") from error
        if not isinstance(mappings, dict):
            raise CogneeError("Cognee project registry is invalid")
    value = _load_env(_config_path()).get("COGNEE_PROJECT_NAME")
    entry = mappings.get(str(canonical))
    if value is None and isinstance(entry, str):
        value = entry
    if value is None and isinstance(entry, dict):
        value = entry.get("dataset_name")
    if value is None:
        raise CogneeError("Cognee project is not explicitly registered")
    if not isinstance(value, str) or not PROJECT_NAME.fullmatch(value):
        raise CogneeError("Cognee project identity is invalid")
    return value


def handoff_content(handoff_id: str, capsule: str, key_fact: str) -> str:
    return f"Pennix formal handoff {handoff_id}.\nVerified key fact: {key_fact}\n\n{capsule}"


def _load_target(project_root: Path) -> tuple[str, str, str, str | None]:
    config = _load_env(_config_path())
    api_url = config.get("COGNEE_BASE_URL")
    token = config.get("COGNEE_API_KEY")
    if not isinstance(api_url, str) or not api_url.startswith(("http://", "https://")):
        raise CogneeError("Cognee API URL is unavailable")
    if not isinstance(token, str) or not token.strip():
        raise CogneeError("Cognee API key is unavailable")
    return api_url.rstrip("/"), token, _project_name(project_root), config.get("COGNEE_DATASET_ID")


class CogneeClient:
    def __init__(self, api_url: str, token: str, project: str, dataset_id: str | None = None, timeout: float = 120.0) -> None:
        self.base = api_url.rstrip("/")
        self.token = token
        self.project = project
        self.dataset_id = dataset_id
        self.timeout = timeout

    @classmethod
    def for_project(cls, project_root: Path) -> "CogneeClient":
        api_url, token, project, dataset_id = _load_target(project_root)
        return cls(api_url, token, project, dataset_id)

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.base + path, data=encoded, method=method, headers={"Accept": "application/json", "Authorization": "Bearer " + self.token, **({"Content-Type": "application/json"} if encoded is not None else {})})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise CogneeError(f"Cognee API request failed: {method} {path}") from error
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CogneeError(f"Cognee API returned invalid JSON: {method} {path}") from error

    def _multipart(self, fields: list[tuple[str, str]], raw_text: str) -> Any:
        boundary = "----pennix-cognee-" + uuid.uuid4().hex
        chunks: list[bytes] = []
        for name, value in [*fields, ("raw_data", raw_text)]:
            chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), value.encode("utf-8"), b"\r\n"])
        chunks.append(f"--{boundary}--\r\n".encode())
        request = urllib.request.Request(self.base + "/api/v1/add", data=b"".join(chunks), method="POST", headers={"Accept": "application/json", "Authorization": "Bearer " + self.token, "Content-Type": f"multipart/form-data; boundary={boundary}"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CogneeError("Cognee handoff add request failed") from error

    def _datasets(self) -> list[dict[str, Any]]:
        value = self._request("GET", "/api/v1/datasets")
        rows = value.get("datasets") if isinstance(value, dict) else value
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise CogneeError("Cognee dataset listing is invalid")
        return rows

    def _dataset_id(self) -> str:
        if self.dataset_id:
            return self.dataset_id
        matches = [row for row in self._datasets() if row.get("name") == self.project and isinstance(row.get("id"), str)]
        if len(matches) != 1:
            raise CogneeError("Cognee project dataset is not uniquely available")
        self.dataset_id = matches[0]["id"]
        return self.dataset_id

    def _data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            value = self._request("GET", f"/api/v1/datasets/{quote(self._dataset_id(), safe='')}/data?" + urlencode({"limit": 1000, "offset": offset}))
            if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
                raise CogneeError("Cognee dataset data listing is invalid")
            rows.extend(value)
            if len(value) < 1000:
                return rows
            offset += len(value)
            if offset > 1_000_000:
                raise CogneeError("Cognee dataset data exceeds the bounded exact scan")

    def _exact_data(self, digest: str, data_id: str | None = None) -> list[dict[str, Any]]:
        matches = []
        for row in self._data():
            metadata = row.get("externalMetadata") or row.get("external_metadata") or {}
            if isinstance(metadata, dict) and metadata.get("pennix_content_sha256") == digest and (data_id is None or str(row.get("id")) == data_id):
                matches.append(row)
        if len(matches) > 1:
            raise CogneeError("Cognee handoff data is not unique")
        return matches

    def _raw(self, data_id: str) -> str:
        request = urllib.request.Request(self.base + f"/api/v1/datasets/{quote(self._dataset_id(), safe='')}/data/{quote(data_id, safe='')}/raw", method="GET", headers={"Accept": "text/plain", "Authorization": "Bearer " + self.token})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeError) as error:
            raise CogneeError("Cognee exact raw read failed") from error

    def retain_handoff(self, handoff_id: str, capsule: str, key_fact: str, *, reconcile_only: bool = False) -> dict[str, Any]:
        content = handoff_content(handoff_id, capsule, key_fact)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if not reconcile_only:
            metadata = {"pennix_kind": "workflow", "pennix_project": self.project, "pennix_handoff_id": handoff_id, "pennix_content_sha256": digest}
            fields = [("datasetName", self.project), ("run_in_background", "false"), ("external_metadata", json.dumps([metadata], ensure_ascii=False))]
            if self.dataset_id:
                fields.append(("datasetId", self.dataset_id))
            write_error: CogneeError | None = None
            try:
                self._multipart(fields, content)
                dataset_id = self._dataset_id()
                result = self._request("POST", "/api/v1/cognify", {"dataset_ids": [dataset_id], "run_in_background": False})
                if isinstance(result, dict) and any(isinstance(value, dict) and value.get("status") == "errored" for value in result.values()):
                    raise CogneeError("Cognee cognify returned an errored pipeline")
            except CogneeError as error:
                write_error = error
        else:
            write_error = None
        matches = self._exact_data(digest)
        if write_error is not None and len(matches) != 1:
            raise write_error
        if len(matches) != 1 or not isinstance(matches[0].get("id"), str):
            raise CogneeError("Cognee handoff write outcome is not uniquely exact-readable")
        return {"data_id": matches[0]["id"], "dataset_id": self._dataset_id(), "content": content, "content_sha256": digest, "project": self.project}

    def verify_retrieval(self, data_id: str, content: str, handoff_id: str) -> int:
        raw = self._raw(data_id)
        if raw != content or hashlib.sha256(raw.encode("utf-8")).hexdigest() != hashlib.sha256(content.encode("utf-8")).hexdigest() or f"Pennix formal handoff {handoff_id}." not in raw:
            raise CogneeError("Cognee handoff raw retrieval did not prove exact content")
        if len(self._exact_data(hashlib.sha256(content.encode("utf-8")).hexdigest(), data_id)) != 1:
            raise CogneeError("Cognee handoff metadata retrieval was not unique")
        return 1

    def improve(self, *, session_ids: list[str] | None = None) -> dict[str, Any]:
        return self._request("POST", "/api/v1/improve", {"dataset_id": self._dataset_id(), "session_ids": session_ids or [], "build_truth_subspace": True, "build_global_context_index": True, "run_in_background": False})
