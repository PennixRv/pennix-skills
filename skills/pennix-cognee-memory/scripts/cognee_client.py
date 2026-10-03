"""Minimal authenticated Cognee boundary for formal handoff writes."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CONFIG_PATH = Path(".cognee") / ".env"
REGISTRY_PATH = Path(".config") / "cognee" / "projects.json"


class NoCredentialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CogneeError("Cognee authenticated API redirects are not allowed")


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


def canonical_project_root(project_root: Path) -> Path:
    """Use Git's main worktree as common identity; non-Git roots are explicit."""
    project_root = project_root.resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CogneeError("Git project identity is unavailable") from error
    if result.returncode:
        return project_root
    first = result.stdout.splitlines()[0] if result.stdout else ""
    if not first.startswith("worktree "):
        raise CogneeError("Git common project root is ambiguous")
    return Path(first.removeprefix("worktree ")).resolve()


def _project_entry(project_root: Path) -> dict[str, str]:
    canonical = canonical_project_root(project_root)
    registry = Path.home() / REGISTRY_PATH
    if (not registry.is_file() or registry.is_symlink()
            or any(parent.is_symlink() for parent in registry.absolute().parents)
            or registry.stat().st_mode & 0o077):
        raise CogneeError("Cognee project registry is missing or not private")
    try:
        mappings = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CogneeError("Cognee project registry is unreadable") from error
    entry = mappings.get(str(canonical)) if isinstance(mappings, dict) else None
    required = {"dataset_name", "dataset_id", "principal_id", "base_url"}
    if not isinstance(entry, dict) or set(entry) != required:
        raise CogneeError("Cognee project lacks a verified service registration")
    if any(not isinstance(entry[key], str) or not entry[key] for key in required):
        raise CogneeError("Cognee project registration is invalid")
    if not PROJECT_NAME.fullmatch(entry["dataset_name"]):
        raise CogneeError("Cognee project dataset name is invalid")
    try:
        uuid.UUID(entry["dataset_id"])
        uuid.UUID(entry["principal_id"])
    except ValueError as error:
        raise CogneeError("Cognee registered identity is invalid") from error
    return entry


def handoff_content(handoff_id: str, capsule: str, key_fact: str) -> str:
    return f"Pennix formal handoff {handoff_id}.\nVerified key fact: {key_fact}\n\n{capsule}"



class CogneeClient:
    def __init__(self, api_url: str, token: str, project: str, dataset_id: str | None = None, timeout: float = 120.0) -> None:
        self.base = api_url.rstrip("/")
        self.token = token
        self.project = project
        self.dataset_id = dataset_id
        self.timeout = timeout

    @classmethod
    def for_project(cls, project_root: Path) -> "CogneeClient":
        entry = _project_entry(project_root)
        config = _load_env(_config_path())
        base = config.get("COGNEE_BASE_URL", "").rstrip("/")
        token = config.get("COGNEE_API_KEY", "")
        if base != entry["base_url"] or not token.strip():
            raise CogneeError("Cognee service no longer matches the project registration")
        client = cls(base, token, entry["dataset_name"], entry["dataset_id"])
        principal = client._request("GET", "/api/v1/users/me")
        if not isinstance(principal, dict) or str(principal.get("id")) != entry["principal_id"]:
            raise CogneeError("Cognee principal no longer matches the project registration")
        matches = [row for row in client._datasets() if str(row.get("id")) == entry["dataset_id"]]
        if (len(matches) != 1 or matches[0].get("name") != entry["dataset_name"]
                or str(matches[0].get("owner_id")) != entry["principal_id"]):
            raise CogneeError("Cognee dataset no longer matches the project registration")
        return client

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.base + path, data=encoded, method=method, headers={"Accept": "application/json", "X-Api-Key": self.token, **({"Content-Type": "application/json"} if encoded is not None else {})})
        try:
            with urllib.request.build_opener(NoCredentialRedirect()).open(request, timeout=self.timeout) as response:
                raw = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise CogneeError(f"Cognee API request failed: {method} {path}") from error
        try:
            return json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CogneeError(f"Cognee API returned invalid JSON: {method} {path}") from error

    def _multipart(self, fields: list[tuple[str, str]], raw_text: str, *, route: str = "/api/v1/add") -> Any:
        boundary = "----pennix-cognee-" + uuid.uuid4().hex
        chunks: list[bytes] = []
        for name, value in [*fields, ("raw_data", raw_text)]:
            chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), value.encode("utf-8"), b"\r\n"])
        chunks.append(f"--{boundary}--\r\n".encode())
        request = urllib.request.Request(self.base + route, data=b"".join(chunks), method="POST", headers={"Accept": "application/json", "X-Api-Key": self.token, "Content-Type": f"multipart/form-data; boundary={boundary}"})
        try:
            with urllib.request.build_opener(NoCredentialRedirect()).open(request, timeout=self.timeout) as response:
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
        request = urllib.request.Request(self.base + f"/api/v1/datasets/{quote(self._dataset_id(), safe='')}/data/{quote(data_id, safe='')}/raw", method="GET", headers={"Accept": "text/plain", "X-Api-Key": self.token})
        try:
            with urllib.request.build_opener(NoCredentialRedirect()).open(request, timeout=self.timeout) as response:
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

    def remember(self, text: str, *, task: str, host_session: str, source: str,
                 kind: str = "decision", approval_ref: str | None = None,
                 supersedes: str | None = None, scope: str = "project") -> dict[str, Any]:
        if not all(isinstance(value, str) and value.strip() for value in (text, task, host_session, source)):
            raise CogneeError("Semantic record requires text, task, host session and source")
        if scope not in {"project", "cross_project", "user"} or (scope != "project" and not approval_ref):
            raise CogneeError("Memory promotion requires an explicit approval reference")
        metadata = {"pennix_kind": kind, "pennix_project": self.project,
                    "task": task, "host_session": host_session, "source": source,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "scope": scope, "approval_ref": approval_ref, "supersedes": supersedes}
        content = "Pennix semantic record\n" + json.dumps(metadata, ensure_ascii=False, sort_keys=True) + "\n\n" + text
        digest = hashlib.sha256(content.encode()).hexdigest()
        metadata["pennix_content_sha256"] = digest
        result = self._multipart([
            ("datasetName", self.project), ("datasetId", self._dataset_id()),
            ("run_in_background", "false"),
            ("external_metadata", json.dumps([metadata], ensure_ascii=False)),
        ], content, route="/api/v1/remember")
        matches = self._exact_data(digest)
        if len(matches) != 1 or self._raw(str(matches[0]["id"])) != content:
            raise CogneeError("Semantic record is not uniquely exact-readable")
        return {"data_id": str(matches[0]["id"]), "dataset_id": self._dataset_id(),
                "content_sha256": digest, "exact_verified": True, "pipeline": result}

    def delete_record(self, data_id: str) -> None:
        uuid.UUID(data_id)
        if len([row for row in self._data() if str(row.get("id")) == data_id]) != 1:
            raise CogneeError("Deletion target is not uniquely present in the registered dataset")
        self._request("DELETE", f"/api/v1/datasets/{quote(self._dataset_id(), safe='')}/data/{data_id}")
        if any(str(row.get("id")) == data_id for row in self._data()):
            raise CogneeError("Deletion is not confirmed by the dataset listing")

    def recall(self, query: str) -> Any:
        return self._request("POST", "/api/v1/recall", {
            "query": query, "dataset_ids": [self._dataset_id()],
            "search_type": "GRAPH_COMPLETION", "include_references": True})

    def promote_record(self, data_id: str, *, scope: str, approval_ref: str,
                       task: str, host_session: str) -> dict[str, Any]:
        if scope not in {"cross_project", "user"} or not approval_ref.strip():
            raise CogneeError("Promotion requires explicit target scope and approval")
        uuid.UUID(data_id)
        if len([row for row in self._data() if str(row.get("id")) == data_id]) != 1:
            raise CogneeError("Promotion source is not uniquely in the registered project")
        text = self._raw(data_id)
        principal = self._request("GET", "/api/v1/users/me")
        principal_id = str(uuid.UUID(principal["id"]))
        name = "pennix-approved-" + scope + "-" + principal_id[:12]
        dataset = self._request("POST", "/api/v1/datasets", {"name": name})
        if dataset.get("owner_id") != principal_id or dataset.get("name") != name:
            raise CogneeError("Promotion target is not owned by the verified principal")
        target = CogneeClient(self.base, self.token, name, dataset["id"], self.timeout)
        return target.remember(text, task=task, host_session=host_session,
            source=f"project:{self.project}/data:{data_id}", approval_ref=approval_ref,
            kind="approved_knowledge" if scope == "cross_project" else "preference", scope=scope)

    def revise_record(self, data_id: str, text: str, *, task: str,
                      host_session: str, source: str) -> dict[str, Any]:
        if len([row for row in self._data() if str(row.get("id")) == data_id]) != 1:
            raise CogneeError("Revision target is not uniquely in the registered dataset")
        result = self.remember(text, task=task, host_session=host_session,
                               source=source, kind="correction", supersedes=data_id)
        self.delete_record(data_id)
        result["superseded_data_id"] = data_id
        return result
