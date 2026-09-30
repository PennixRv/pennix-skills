"""Private local configuration adapters for lifecycle-declared owner targets."""

from __future__ import annotations

import json
import hashlib
import os
import errno
import re
import shutil
import stat
import subprocess
import tempfile
import termios
from pathlib import Path
from typing import Any


MAX_CONFIG_BYTES = 64 * 1024
PROFILE_SCHEMA = 1
MARKER_KEY = "pennixLifecycle"
STATE_DIRECTORY = "pennix-workflow-lifecycle"
AGENTMEMORY_RECEIPT = "agentmemory-config.json"
AGENTMEMORY_CONFIG_RELATIVE = (".config", "agentmemory", "client.env")
AGENTMEMORY_PROJECTS_RELATIVE = (".config", "agentmemory", "projects.json")
PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class ConfigurationError(RuntimeError):
    """Raised without including configuration values or file contents."""


def _xdg_config_home() -> Path:
    raw = os.environ.get("XDG_CONFIG_HOME")
    return Path(raw).expanduser() if raw else Path.home() / ".config"


def _home() -> Path:
    raw = os.environ.get("HOME")
    return Path(raw).expanduser() if raw else Path.home()


def _assert_no_symlink_ancestor(path: Path) -> None:
    current = path.absolute()
    while current != current.parent:
        if current.is_symlink():
            raise ConfigurationError("configuration path is blocked")
        current = current.parent


def state_root() -> Path:
    raw = os.environ.get("XDG_STATE_HOME")
    base = Path(raw).expanduser() if raw else Path.home() / ".local" / "state"
    if not base.is_absolute():
        raise ConfigurationError("XDG state directory must be absolute")
    root = base / STATE_DIRECTORY
    _assert_no_symlink_ancestor(root)
    return root


def state_namespace(codex_home: Path) -> Path:
    try:
        resolved = codex_home.resolve(strict=False)
    except OSError as error:
        raise ConfigurationError("CODEX_HOME cannot be resolved safely") from error
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()
    namespace = state_root() / "homes" / digest
    _assert_no_symlink_ancestor(namespace)
    return namespace


def ensure_state_namespace(namespace: Path) -> Path:
    root = namespace.parents[1]
    homes = namespace.parent
    for directory in (root, homes, namespace):
        _assert_no_symlink_ancestor(directory)
        directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        metadata = directory.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise ConfigurationError("lifecycle state directory is unsafe")
        if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
            raise ConfigurationError("lifecycle state directory owner is unsafe")
    return namespace


def ensure_state_directory(codex_home: Path) -> Path:
    return ensure_state_namespace(state_namespace(codex_home))


def _private_file(path: Path) -> tuple[str, bytes | None]:
    try:
        _assert_no_symlink_ancestor(path)
        nofollow = getattr(os, "O_NOFOLLOW", None)
        if nofollow is None:
            return "blocked", None
        descriptor = os.open(path, os.O_RDONLY | nofollow)
    except FileNotFoundError:
        return "missing", None
    except OSError as error:
        return ("blocked", None) if error.errno == errno.ELOOP else ("unknown", None)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_CONFIG_BYTES or metadata.st_mode & 0o077:
            return "blocked", None
        with os.fdopen(descriptor, "rb") as handle:
            value = handle.read(MAX_CONFIG_BYTES + 1)
        descriptor = -1
    except OSError:
        return "invalid", None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(value) > MAX_CONFIG_BYTES:
        return "blocked", None
    return "configured", value


def _private_json(path: Path, required: set[str] | None = None) -> tuple[str, dict[str, Any] | None]:
    state, content = _private_file(path)
    if state != "configured" or content is None:
        return state, None
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid", None
    if not isinstance(value, dict) or (required and any(not isinstance(value.get(key), str) or not value[key].strip() for key in required)):
        return "invalid", None
    return "configured", value


def _write_private_json(path: Path, value: dict[str, Any]) -> None:
    _assert_no_symlink_ancestor(path)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        metadata = None
    except OSError as error:
        raise ConfigurationError("configuration target is blocked") from error
    if metadata is not None and (
        stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077
    ):
        raise ConfigurationError("configuration target is blocked")
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ConfigurationError("configuration target is blocked")
    os.chmod(path.parent, 0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def profile_path(codex_home: Path) -> Path:
    return state_namespace(codex_home) / "profile.json"


def legacy_state_root(codex_home: Path) -> Path:
    return codex_home / STATE_DIRECTORY


def legacy_profile_path(codex_home: Path) -> Path:
    return legacy_state_root(codex_home) / "profile.json"


def static_receipt_path(codex_home: Path, asset: str) -> Path:
    return state_namespace(codex_home) / "static-assets" / f"{asset}.json"


def agentmemory_config_path() -> Path:
    raw = os.environ.get("AGENTMEMORY_CLIENT_CONFIG")
    path = Path(raw).expanduser() if raw else _home().joinpath(*AGENTMEMORY_CONFIG_RELATIVE)
    if not path.is_absolute():
        raise ConfigurationError("AgentMemory config path must be absolute")
    return path


def _write_text_atomic(path: Path, content: str) -> None:
    _assert_no_symlink_ancestor(path)
    path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ConfigurationError("configuration path is blocked")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _agentmemory_receipt(codex_home: Path) -> tuple[str, dict[str, Any] | None]:
    return _private_json(static_receipt_path(codex_home, "agentmemory-config"))


def _read_env(path: Path) -> tuple[str, dict[str, str] | None]:
    state, content = _private_file(path)
    if state != "configured" or content is None:
        return state, None
    values: dict[str, str] = {}
    try:
        for line in content.decode("utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
                return "invalid", None
            values[key] = value
    except UnicodeDecodeError:
        return "invalid", None
    return "configured", values


def _write_env(path: Path, values: dict[str, str]) -> None:
    _assert_no_symlink_ancestor(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(path.parent, 0o700)
    _write_text_atomic(path, "".join(f"{key}={values[key]}\n" for key in sorted(values)))
    os.chmod(path, 0o600)


def agentmemory_policy(api_url: str) -> dict[str, str]:
    if not isinstance(api_url, str) or not api_url.strip() or not api_url.startswith(("http://", "https://")):
        raise ConfigurationError("AgentMemory API URL is invalid")
    return {"AGENTMEMORY_URL": api_url.rstrip("/"), "AGENTMEMORY_INJECT_CONTEXT": "true"}


def agentmemory_static_state(codex_home: Path, api_url: str) -> str:
    state, data = _read_env(agentmemory_config_path())
    if state == "missing":
        return "not-configured"
    if state != "configured" or data is None:
        return state
    receipt_state, receipt = _agentmemory_receipt(codex_home)
    expected = agentmemory_policy(api_url)
    return "configured" if receipt_state == "configured" and receipt and receipt.get("fields") == expected and all(data.get(k) == v for k, v in expected.items()) else "drifted"


def configure_agentmemory_static(codex_home: Path, api_url: str) -> str:
    path = agentmemory_config_path()
    state, current = _read_env(path)
    if state not in {"missing", "configured"}:
        raise ConfigurationError("AgentMemory client configuration is blocked")
    policy = agentmemory_policy(api_url)
    data = current or {}
    receipt_state, receipt = _agentmemory_receipt(codex_home)
    if receipt_state == "invalid":
        raise ConfigurationError("AgentMemory lifecycle ownership receipt is invalid")
    if receipt_state == "configured" and receipt and any(data.get(k) != v for k, v in receipt["fields"].items()):
        raise ConfigurationError("AgentMemory client configuration was modified outside lifecycle")
    data.update(policy)
    _write_env(path, data)
    _write_private_json(static_receipt_path(codex_home, "agentmemory-config"), {"schema": 1, "path": str(path), "fields": policy})
    return "configured"


def configure_agentmemory_secret(codex_home: Path) -> str:
    receipt_state, receipt = _agentmemory_receipt(codex_home)
    if receipt_state != "configured" or not receipt:
        raise ConfigurationError("AgentMemory static policy is not ready")
    path = agentmemory_config_path()
    state, data = _read_env(path)
    if state != "configured" or data is None:
        raise ConfigurationError("AgentMemory client configuration is not ready")
    data["AGENTMEMORY_SECRET"] = _read_tty("AgentMemory service secret: ", secret=True)
    _write_env(path, data)
    return "configured"


def agentmemory_secret_state(codex_home: Path) -> str:
    state, data = _read_env(agentmemory_config_path())
    if state == "missing":
        return "not-configured"
    if state != "configured" or data is None:
        return state
    return "configured" if data.get("AGENTMEMORY_SECRET", "").strip() else "not-configured"


def remove_agentmemory_configuration(codex_home: Path) -> str:
    receipt_state, receipt = _agentmemory_receipt(codex_home)
    if receipt_state == "missing":
        return "no-op"
    if receipt_state != "configured" or receipt is None:
        raise ConfigurationError("AgentMemory lifecycle ownership receipt is blocked")
    path = agentmemory_config_path()
    state, data = _read_env(path)
    if state != "configured" or data is None or any(data.get(k) != v for k, v in receipt["fields"].items()):
        raise ConfigurationError("AgentMemory client configuration is blocked")
    for key in (*receipt["fields"].keys(), "AGENTMEMORY_SECRET"):
        data.pop(key, None)
    if data:
        _write_env(path, data)
    else:
        path.unlink(missing_ok=True)
    static_receipt_path(codex_home, "agentmemory-config").unlink(missing_ok=True)
    return "changed"


def disable_targets(codex_home: Path, catalog_digest: str, target_ids: set[str]) -> None:
    state, targets = load_profile(codex_home, catalog_digest)
    if state not in {"missing", "match", "stale"}:
        raise ConfigurationError("profile record is blocked")
    remaining = targets - target_ids
    if not remaining:
        profile = profile_path(codex_home)
        profile.unlink(missing_ok=True)
        return
    ensure_state_directory(codex_home)
    _write_private_json(
        profile_path(codex_home),
        {"schema": PROFILE_SCHEMA, "catalog_digest": catalog_digest, "targets": sorted(remaining)},
    )


def register_agentmemory_project(codex_home: Path, project_root: Path) -> str:
    if project_root.is_symlink() or not project_root.is_dir():
        raise ConfigurationError("project root is ambiguous")
    name = project_root.name
    if not PROJECT_NAME.fullmatch(name):
        raise ConfigurationError("project name is invalid")
    path = _home().joinpath(*AGENTMEMORY_PROJECTS_RELATIVE)
    state, data = _private_json(path)
    if state not in {"missing", "configured"}:
        raise ConfigurationError("AgentMemory project registry is blocked")
    mappings = data or {}
    canonical = str(project_root.resolve())
    existing = mappings.get(canonical)
    if existing is not None and existing != name:
        raise ConfigurationError("AgentMemory project mapping conflicts")
    mappings[canonical] = name
    _write_private_json(path, mappings)
    return name


def unregister_agentmemory_project(project_root: Path) -> str:
    path = _home().joinpath(*AGENTMEMORY_PROJECTS_RELATIVE)
    state, data = _private_json(path)
    if state != "configured" or data is None:
        return "no-op"
    canonical = str(project_root.resolve())
    if canonical not in data:
        return "no-op"
    del data[canonical]
    if data:
        _write_private_json(path, data)
    else:
        path.unlink(missing_ok=True)
    return "changed"


def load_profile(codex_home: Path, catalog_digest: str) -> tuple[str, set[str]]:
    state, value = _private_json(profile_path(codex_home))
    if state == "missing":
        return "missing", set()
    if state != "configured" or value is None:
        return state, set()
    targets = value.get("targets")
    if value.get("schema") != PROFILE_SCHEMA or not isinstance(targets, list):
        return "drifted", set()
    if any(not isinstance(target, str) for target in targets) or len(targets) != len(set(targets)):
        return "invalid", set()
    if value.get("catalog_digest") != catalog_digest:
        return "stale", set(targets)
    return "match", set(targets)


def enable_target(codex_home: Path, catalog_digest: str, target: str) -> set[str]:
    state, targets = load_profile(codex_home, catalog_digest)
    if state not in {"missing", "match", "stale"}:
        raise ConfigurationError("profile record is blocked")
    targets.add(target)
    ensure_state_directory(codex_home)
    _write_private_json(
        profile_path(codex_home),
        {"schema": PROFILE_SCHEMA, "catalog_digest": catalog_digest, "targets": sorted(targets)},
    )
    return targets


def _read_tty(prompt: str, secret: bool = False) -> str:
    try:
        descriptor = os.open("/dev/tty", os.O_RDWR | getattr(os, "O_NOCTTY", 0))
        with os.fdopen(descriptor, "r", encoding="utf-8", buffering=1) as terminal, os.fdopen(
            os.dup(descriptor), "w", encoding="utf-8", buffering=1
        ) as writer:
            writer.write(prompt)
            writer.flush()
            original = termios.tcgetattr(descriptor) if secret else None
            if original is not None:
                hidden = original[:]
                hidden[3] &= ~termios.ECHO
                termios.tcsetattr(descriptor, termios.TCSADRAIN, hidden)
            try:
                value = terminal.readline().strip()
            finally:
                if original is not None:
                    termios.tcsetattr(descriptor, termios.TCSADRAIN, original)
                    writer.write("\n")
                    writer.flush()
    except OSError as error:
        raise ConfigurationError("local-input-required") from error
    if not value:
        raise ConfigurationError("local input was empty")
    return value


def _run_owner(command: list[str]) -> None:
    if not shutil.which(command[0]):
        raise ConfigurationError("owner command is unavailable")
    try:
        with open("/dev/tty", "r+", encoding="utf-8") as terminal:
            result = subprocess.run(command, stdin=terminal, stdout=terminal, stderr=terminal, check=False)
    except OSError as error:
        raise ConfigurationError("local-input-required") from error
    if result.returncode:
        raise ConfigurationError("owner configuration did not complete")


def _grok_path() -> Path:
    return _xdg_config_home() / "grok-search" / "config.json"


def _hikari_path() -> Path:
    return _xdg_config_home() / "tavily-hikari-cli" / "config.json"


def _cch_paths() -> tuple[Path, Path]:
    directory = _xdg_config_home() / "cch-codex-tmux-status"
    return directory / "config.json", directory / "cch-token"


def target_state(adapter: str, codex_home: Path, settings: dict[str, Any] | None = None) -> str:
    if adapter == "codex-provider":
        auth = codex_home / "auth.json"
        state, content = _private_file(auth)
        return "ready" if state == "configured" and content else state.replace("missing", "not-configured")
    if adapter == "cch-owner":
        config, token = _cch_paths()
        config_state, _ = _private_json(config)
        token_state, token_content = _private_file(token)
        if config_state == "configured" and token_state == "configured" and token_content:
            return "configured"
        return "not-configured" if "missing" in {config_state, token_state} else "blocked"
    if adapter == "windsurf-owner":
        command = shutil.which("windsurf-code-search")
        if not command:
            return "unknown"
        try:
            result = subprocess.run([command, "config-doctor"], capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return "unknown"
        return "configured" if result.returncode == 0 and result.stdout.strip() == "status=configured" else "not-configured"
    if adapter == "hikari-json":
        return _private_json(_hikari_path(), {"baseUrl", "token"})[0].replace("missing", "not-configured")
    if adapter.startswith("grok-"):
        state, value = _private_json(_grok_path())
        if state != "configured" or value is None:
            return state.replace("missing", "not-configured")
        if value.get(MARKER_KEY) != 1:
            return "drifted"
        required = {"grok-provider": {"apiUrl", "apiKey"}, "grok-tavily": {"tavilyApiKey"}, "grok-firecrawl": {"firecrawlApiKey"}}[adapter]
        return "configured" if all(isinstance(value.get(key), str) and value[key].strip() for key in required) else "not-configured"
    if adapter == "agentmemory-static":
        api_url = (settings or {}).get("apiUrl") or os.environ.get("PENNIX_AGENTMEMORY_API_URL")
        if not isinstance(api_url, str) or not api_url.strip():
            return "blocked"
        try:
            return agentmemory_static_state(codex_home, api_url)
        except ConfigurationError:
            return "blocked"
    if adapter == "agentmemory-secret":
        try:
            return agentmemory_secret_state(codex_home)
        except ConfigurationError:
            return "blocked"
    if adapter == "agentmemory-project":
        state, data = _private_json(_home().joinpath(*AGENTMEMORY_PROJECTS_RELATIVE))
        return "configured" if state == "configured" and data else "not-configured" if state == "missing" else state
    return "unknown"


def configure_target(
    adapter: str,
    codex_home: Path,
    settings: dict[str, Any] | None = None,
    project_root: Path | None = None,
    unregister: bool = False,
) -> str:
    if adapter == "codex-provider":
        _run_owner(["codex", "login"])
        return target_state(adapter, codex_home)
    if adapter == "cch-owner":
        _run_owner(["cch-codex-tmux-status", "configure"])
        return target_state(adapter, codex_home)
    if adapter == "windsurf-owner":
        _run_owner(["windsurf-code-search", "configure"])
        return target_state(adapter, codex_home)
    if adapter == "agentmemory-static":
        api_url = (settings or {}).get("apiUrl") or os.environ.get("PENNIX_AGENTMEMORY_API_URL")
        if not isinstance(api_url, str):
            raise ConfigurationError("AgentMemory API URL is required")
        return configure_agentmemory_static(codex_home, api_url)
    if adapter == "agentmemory-secret":
        return configure_agentmemory_secret(codex_home)
    if adapter == "agentmemory-project":
        if project_root is None:
            raise ConfigurationError("project root is required")
        return unregister_agentmemory_project(project_root) if unregister else "configured" if register_agentmemory_project(codex_home, project_root) else "blocked"
    if adapter == "hikari-json":
        base_url = _read_tty("Hikari endpoint: ")
        token = _read_tty("Hikari access token: ", secret=True)
        _write_private_json(_hikari_path(), {"baseUrl": base_url.rstrip("/"), "token": token, MARKER_KEY: 1})
        return target_state(adapter, codex_home)
    if adapter.startswith("grok-"):
        state, value = _private_json(_grok_path())
        if state not in {"missing", "configured"}:
            raise ConfigurationError("Grok configuration is blocked")
        data = value or {}
        if data and data.get(MARKER_KEY) != 1:
            raise ConfigurationError("Grok configuration is user-owned or drifted")
        data[MARKER_KEY] = 1
        if adapter == "grok-provider":
            data["apiUrl"] = _read_tty("Grok API endpoint: ").rstrip("/")
            data["apiKey"] = _read_tty("Grok API key: ", secret=True)
        elif adapter == "grok-tavily":
            data["tavilyApiKey"] = _read_tty("Tavily API key: ", secret=True)
        else:
            data["firecrawlApiKey"] = _read_tty("Firecrawl API key: ", secret=True)
        _write_private_json(_grok_path(), data)
        return target_state(adapter, codex_home)
    raise ConfigurationError("unknown configuration adapter")
