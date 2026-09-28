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
HINDSIGHT_RECEIPT = "hindsight-config.json"
HINDSIGHT_CONFIG_RELATIVE = (".hindsight", "coding-agent.json")
HINDSIGHT_RUNTIME_RELATIVE = (".hindsight", "coding-agents")
PROJECT_BANK_ID = re.compile(r"^pennix-project-[0-9a-f]{16,64}$")


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


def hindsight_config_path() -> Path:
    raw = os.environ.get("HINDSIGHT_CONFIG")
    path = Path(raw).expanduser() if raw else _home().joinpath(*HINDSIGHT_CONFIG_RELATIVE)
    if not path.is_absolute():
        raise ConfigurationError("Hindsight config path must be absolute")
    return path


def hindsight_runtime_path() -> Path:
    return _home().joinpath(*HINDSIGHT_RUNTIME_RELATIVE)


def assert_hindsight_codex_home(codex_home: Path) -> None:
    expected = (_home() / ".codex").resolve(strict=False)
    actual = codex_home.resolve(strict=False)
    configured = os.environ.get("CODEX_HOME")
    if actual != expected or (configured and Path(configured).expanduser().resolve(strict=False) != expected):
        raise ConfigurationError("Hindsight 0.7.0 requires the default HOME/.codex location")


def hindsight_receipt_path(codex_home: Path) -> Path:
    return static_receipt_path(codex_home, "hindsight-config")


def hindsight_policy(api_url: str) -> dict[str, Any]:
    if not isinstance(api_url, str) or not api_url.strip() or not api_url.startswith(("http://", "https://")):
        raise ConfigurationError("Hindsight API URL is invalid")
    return {
        "serverMode": "self-hosted",
        "apiUrl": api_url.rstrip("/"),
        "optInOnly": True,
        "autoInject": "pages",
        "pageTriggerType": "cron",
        "pageTriggerCron": "H 3 * * *",
        "autoUpdate": False,
        "autoSeed": False,
        "codebaseSurvey": False,
        "gitIngest": "none",
        "retainSessions": True,
    }


def _legacy_hindsight_policy(api_url: str) -> dict[str, Any]:
    if not isinstance(api_url, str) or not api_url.strip() or not api_url.startswith(("http://", "https://")):
        raise ConfigurationError("Hindsight API URL is invalid")
    return {
        "serverMode": "self-hosted",
        "apiUrl": api_url.rstrip("/"),
        "optInOnly": True,
        "autoReflect": True,
        "autoUpdate": False,
        "autoSeed": False,
        "codebaseSurvey": False,
        "gitIngest": "none",
        "retainSessions": True,
    }


def _hindsight_values(data: dict[str, Any], fields: dict[str, Any]) -> bool:
    return all(data.get(key) == value for key, value in fields.items())


def _hindsight_receipt(codex_home: Path) -> tuple[str, dict[str, Any] | None]:
    state, value = _private_json(hindsight_receipt_path(codex_home))
    if state != "configured" or value is None:
        return state, value
    fields = value.get("fields")
    if not isinstance(fields, dict) or not fields:
        return "invalid", None
    try:
        if value.get("schema") == 2:
            expected = hindsight_policy(fields.get("apiUrl"))
            receipt_state = "configured"
        elif value.get("schema") == 1:
            expected = _legacy_hindsight_policy(fields.get("apiUrl"))
            receipt_state = "legacy"
        else:
            return "invalid", None
    except ConfigurationError:
        return "invalid", None
    if fields != expected:
        return "invalid", None
    return receipt_state, value


def hindsight_static_state(codex_home: Path, api_url: str) -> str:
    config_state, data = _private_json(hindsight_config_path())
    if config_state == "missing":
        return "not-configured"
    if config_state != "configured" or data is None:
        return config_state
    receipt_state, receipt = _hindsight_receipt(codex_home)
    if receipt_state != "configured" or receipt is None:
        return "drifted"
    expected = hindsight_policy(api_url)
    owned = receipt.get("fields")
    if owned != expected or not _hindsight_values(data, expected):
        return "drifted"
    return "configured"


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


def configure_hindsight_static(codex_home: Path, api_url: str, claim_upstream: bool = False) -> str:
    path = hindsight_config_path()
    state, current = _private_json(path)
    if state not in {"missing", "configured"}:
        raise ConfigurationError("Hindsight config is blocked")
    data = current or {}
    policy = hindsight_policy(api_url)
    receipt_state, receipt = _hindsight_receipt(codex_home)
    if receipt_state == "invalid":
        raise ConfigurationError("Hindsight lifecycle ownership receipt is invalid")
    if receipt_state in {"configured", "legacy"} and receipt is not None:
        previous = receipt["fields"]
        if not _hindsight_values(data, previous):
            raise ConfigurationError("Hindsight static configuration was modified outside lifecycle")
    elif state == "configured":
        if not claim_upstream or not _hindsight_values(
            data, {"serverMode": policy["serverMode"], "apiUrl": policy["apiUrl"]}
        ):
            raise ConfigurationError("existing Hindsight config has no lifecycle ownership")
    data.update(policy)
    data.pop("autoReflect", None)
    _write_private_json(path, data)
    _write_private_json(
        hindsight_receipt_path(codex_home),
        {"schema": 2, "path": str(path), "fields": policy},
    )
    return "configured"


def configure_hindsight_token(codex_home: Path) -> str:
    receipt_state, receipt = _hindsight_receipt(codex_home)
    if receipt_state not in {"configured", "legacy"} or receipt is None:
        raise ConfigurationError("Hindsight static policy is not ready")
    if hindsight_static_state(codex_home, str(receipt["fields"]["apiUrl"])) != "configured":
        raise ConfigurationError("Hindsight static policy is not ready")
    path = hindsight_config_path()
    state, data = _private_json(path)
    if state != "configured" or data is None:
        raise ConfigurationError("Hindsight config is not ready")
    token = _read_tty("Hindsight API token: ", secret=True)
    data["apiToken"] = token
    _write_private_json(path, data)
    return "configured"


def hindsight_token_state(codex_home: Path) -> str:
    state, data = _private_json(hindsight_config_path())
    if state == "missing":
        return "not-configured"
    if state != "configured" or data is None:
        return state
    token = data.get("apiToken")
    return "configured" if isinstance(token, str) and token.strip() else "not-configured"


def remove_hindsight_configuration(codex_home: Path) -> str:
    receipt_state, receipt = _hindsight_receipt(codex_home)
    if receipt_state == "missing":
        return "no-op"
    if receipt_state != "configured" or receipt is None:
        raise ConfigurationError("Hindsight lifecycle ownership receipt is blocked")
    path = hindsight_config_path()
    state, data = _private_json(path)
    if state != "configured" or data is None:
        raise ConfigurationError("Hindsight config is blocked")
    fields = receipt["fields"]
    if not _hindsight_values(data, fields):
        raise ConfigurationError("Hindsight static configuration was modified outside lifecycle")
    for key in (*fields.keys(), "apiToken"):
        data.pop(key, None)
    _write_private_json(path, data)
    receipt_path = hindsight_receipt_path(codex_home)
    receipt_path.unlink(missing_ok=True)
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


def _project_config_path(project_root: Path) -> Path:
    if project_root.is_symlink() or not project_root.is_dir():
        raise ConfigurationError("project root is ambiguous")
    path = project_root / ".trellis" / "config.yaml"
    if path.is_symlink() or not path.is_file():
        raise ConfigurationError("Trellis config is missing or unsafe")
    return path


def _project_bank_id(text: str) -> str | None:
    lines = text.splitlines()
    hits: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        if line.strip() == "pennix:":
            pennix_indent = len(line) - len(line.lstrip(" "))
            for memory_index in range(index + 1, len(lines)):
                candidate = lines[memory_index]
                if candidate.strip() and len(candidate) - len(candidate.lstrip(" ")) <= pennix_indent:
                    break
                if candidate.strip() == "memory:":
                    memory_indent = len(candidate) - len(candidate.lstrip(" "))
                    for bank_index in range(memory_index + 1, len(lines)):
                        bank = lines[bank_index]
                        if bank.strip() and len(bank) - len(bank.lstrip(" ")) <= memory_indent:
                            break
                        match = re.match(r"^\s+bank_id:\s*([\"']?)([^\"' #]+)\1\s*$", bank)
                        if match:
                            hits.append((memory_index, bank_index, match.group(2)))
                    break
    if len(hits) > 1 or (hits and not PROJECT_BANK_ID.fullmatch(hits[0][2])):
        raise ConfigurationError("Trellis project bank identity is ambiguous")
    return hits[0][2] if hits else None


def _add_project_bank_id(path: Path, text: str, bank_id: str) -> str:
    if "\r\n" in text:
        newline = "\r\n"
    else:
        newline = "\n"
    if "pennix:" in text:
        raise ConfigurationError("Trellis pennix config block is unsupported or incomplete")
    suffix = "" if not text or text.endswith(("\n", "\r")) else newline
    return text + suffix + newline.join(("# Pennix Hindsight project memory identity", "pennix:", "  memory:", f"    bank_id: {bank_id}", ""))


def register_hindsight_project(codex_home: Path, project_root: Path) -> str:
    path = _project_config_path(project_root)
    text = path.read_text(encoding="utf-8")
    bank_id = _project_bank_id(text)
    updated = text
    if bank_id is None:
        bank_id = "pennix-project-" + hashlib.sha256(str(project_root.resolve()).encode("utf-8")).hexdigest()[:24]
        updated = _add_project_bank_id(path, text, bank_id)
    config_path = hindsight_config_path()
    state, data = _private_json(config_path)
    if state != "configured" or data is None:
        raise ConfigurationError("Hindsight static config is not ready")
    original_data = json.loads(json.dumps(data))
    mappings = dict(data.get("mapPathToBank", {})) if isinstance(data.get("mapPathToBank", {}), dict) else data.get("mapPathToBank", {})
    if mappings is None:
        mappings = {}
    if not isinstance(mappings, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in mappings.items()):
        raise ConfigurationError("Hindsight path mapping is invalid")
    canonical = str(project_root.resolve())
    for mapped_path, mapped_bank in mappings.items():
        if mapped_path != canonical and mapped_bank == bank_id:
            raise ConfigurationError("Hindsight bank identity is already mapped")
    if canonical in mappings and mappings[canonical] != bank_id:
        raise ConfigurationError("Hindsight project mapping conflicts")
    mappings[canonical] = bank_id
    data = dict(data)
    data["mapPathToBank"] = mappings
    try:
        if updated != text:
            _write_text_atomic(path, updated)
        _write_private_json(config_path, data)
    except Exception as error:
        try:
            if updated != text:
                _write_text_atomic(path, text)
            _write_private_json(config_path, original_data)
        except Exception as rollback_error:
            raise ConfigurationError("Hindsight project registration rollback failed") from rollback_error
        raise ConfigurationError("Hindsight project registration was not applied") from error
    return bank_id


def unregister_hindsight_project(project_root: Path) -> str:
    path = _project_config_path(project_root)
    text = path.read_text(encoding="utf-8")
    bank_id = _project_bank_id(text)
    if bank_id is None:
        return "no-op"
    config_path = hindsight_config_path()
    state, data = _private_json(config_path)
    if state != "configured" or data is None:
        return "no-op"
    mappings = data.get("mapPathToBank")
    if not isinstance(mappings, dict):
        return "no-op"
    canonical = str(project_root.resolve())
    if canonical not in mappings:
        return "no-op"
    if mappings[canonical] != bank_id:
        raise ConfigurationError("Hindsight project mapping was modified outside lifecycle")
    del mappings[canonical]
    if mappings:
        data["mapPathToBank"] = mappings
    else:
        data.pop("mapPathToBank", None)
    _write_private_json(config_path, data)
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
        with open("/dev/tty", "r+", encoding="utf-8", buffering=1) as terminal:
            terminal.write(prompt)
            terminal.flush()
            original = termios.tcgetattr(terminal.fileno()) if secret else None
            if original is not None:
                hidden = original[:]
                hidden[3] &= ~termios.ECHO
                termios.tcsetattr(terminal.fileno(), termios.TCSADRAIN, hidden)
            try:
                value = terminal.readline().strip()
            finally:
                if original is not None:
                    termios.tcsetattr(terminal.fileno(), termios.TCSADRAIN, original)
                    terminal.write("\n")
                    terminal.flush()
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
    if adapter == "hindsight-static":
        api_url = (settings or {}).get("apiUrl") or os.environ.get("PENNIX_HINDSIGHT_API_URL")
        if not isinstance(api_url, str) or not api_url.strip():
            return "blocked"
        try:
            return hindsight_static_state(codex_home, api_url)
        except ConfigurationError:
            return "blocked"
    if adapter == "hindsight-token":
        try:
            return hindsight_token_state(codex_home)
        except ConfigurationError:
            return "blocked"
    if adapter == "hindsight-project":
        state, data = _private_json(hindsight_config_path())
        if state != "configured" or data is None:
            return "not-configured" if state == "missing" else state
        mappings = data.get("mapPathToBank")
        if not isinstance(mappings, dict):
            return "not-configured"
        return "configured" if any(isinstance(value, str) and PROJECT_BANK_ID.fullmatch(value) for value in mappings.values()) else "not-configured"
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
    if adapter == "hindsight-static":
        api_url = (settings or {}).get("apiUrl") or os.environ.get("PENNIX_HINDSIGHT_API_URL")
        if not isinstance(api_url, str):
            raise ConfigurationError("Hindsight API URL is required")
        return configure_hindsight_static(codex_home, api_url)
    if adapter == "hindsight-token":
        return configure_hindsight_token(codex_home)
    if adapter == "hindsight-project":
        if project_root is None:
            raise ConfigurationError("project root is required")
        return unregister_hindsight_project(project_root) if unregister else "configured" if register_hindsight_project(codex_home, project_root) else "blocked"
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
