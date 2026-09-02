#!/usr/bin/env python3
"""Run recoverable updates for installed Codex plugins that provide hooks."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import selectors
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 2
DEFAULT_TTL_MINUTES = 120
MAX_CAPTURE_BYTES = 2 * 1024 * 1024
APP_SERVER_TIMEOUT_SECONDS = 20
TRANSACTION_ID = re.compile(r"^[0-9a-f]{32}$")
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SELECTOR_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
VERSION_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,127}$")
TRANSACTION_STATES = {
    "prepared",
    "refreshing",
    "refresh_failed",
    "installing",
    "install_failed",
    "restart_required",
    "recovery_required",
    "completed",
    "failed_safe",
    "expired",
    "aborted",
}
ACTIVE_TRANSACTION_STATES = {
    "prepared",
    "refreshing",
    "refresh_failed",
    "installing",
    "install_failed",
    "restart_required",
    "recovery_required",
}
RECOVERY_TOOL_UPDATE_PATHS = {
    "skills/codex-plugin-update/scripts/plugin-update-transaction.py",
    "skills/codex-plugin-update/tests/test_plugin_update_transaction.py",
    "skills/codex-plugin-update/SKILL.md",
    "skills/codex-plugin-update/agents/openai.yaml",
}


class TransactionError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise TransactionError("transaction timestamp is missing")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TransactionError("transaction timestamp is invalid") from exc


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_text(value: str) -> str:
    return digest_bytes(value.encode("utf-8"))


def file_digest(path: Path) -> str | None:
    return digest_bytes(path.read_bytes()) if path.is_file() else None


def code_home() -> Path:
    value = os.environ.get("CODEX_HOME")
    root = Path(value).expanduser() if value else Path.home() / ".codex"
    root = root.resolve()
    if not root.is_dir():
        raise TransactionError(f"CODEX_HOME is not a directory: {root}")
    return root


def transaction_root(root: Path) -> Path:
    return root / ".local-backup" / "plugin-update-transactions"


def ensure_private_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir() or path.resolve() != path:
            raise TransactionError(f"transaction state directory is unsafe: {path}")
    else:
        path.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(path, 0o700)


@contextmanager
def transaction_lock(root: Path) -> Iterator[None]:
    ensure_private_directory(root)
    lock_path = root / ".lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    ensure_private_directory(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=".transaction.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def parse_selector(value: str) -> tuple[str, str]:
    if "@" not in value:
        raise TransactionError("plugin selector must use <plugin>@<marketplace>")
    plugin_name, marketplace = value.rsplit("@", 1)
    if not SELECTOR_PART.fullmatch(plugin_name) or not SELECTOR_PART.fullmatch(marketplace):
        raise TransactionError("plugin selector contains unsupported characters")
    return plugin_name, marketplace


def validate_version(value: str) -> str:
    if not VERSION_VALUE.fullmatch(value) or value in {".", ".."}:
        raise TransactionError("target version contains unsupported characters")
    return value


def session_digest() -> str:
    value = os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
    if not value:
        raise TransactionError("CODEX_THREAD_ID or CODEX_SESSION_ID is required")
    return digest_text(value)


def codex_process_identity() -> dict[str, Any] | None:
    """Return stable Linux metadata for the Codex ancestor process."""
    if sys.platform != "linux":
        return None
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
        boot_time = next(
            int(line.split()[1])
            for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines()
            if line.startswith("btime ")
        )
        clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    except (FileNotFoundError, OSError, StopIteration, ValueError):
        return None

    pid = os.getppid()
    for _ in range(16):
        if pid <= 1:
            return None
        try:
            stat_text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            closing = stat_text.rfind(")")
            if closing < 0:
                return None
            fields = stat_text[closing + 2 :].split()
            parent_pid = int(fields[1])
            start_ticks = int(fields[19])
            command = Path(f"/proc/{pid}/comm").read_text(encoding="utf-8").strip()
        except (FileNotFoundError, OSError, IndexError, ValueError):
            return None
        if command == "codex" or command.startswith("codex-"):
            return {
                "boot_id_digest": digest_text(boot_id),
                "pid": pid,
                "start_ticks": start_ticks,
                "started_at_epoch": boot_time + (start_ticks / clock_ticks),
            }
        pid = parent_pid
    return None


def restart_proven(
    payload: dict[str, Any],
    current_session: str,
    current_process: dict[str, Any] | None,
) -> bool:
    """Prove a post-install Codex restart without treating a thread as a process."""
    origin_process = payload.get("origin_process")
    if isinstance(origin_process, dict) and current_process is not None:
        try:
            boundary = restart_boundary(payload).timestamp()
            started_at = float(current_process["started_at_epoch"])
        except (KeyError, TypeError, ValueError, TransactionError):
            return False
        if started_at <= boundary:
            return False
        identity_fields = ("boot_id_digest", "pid", "start_ticks")
        if all(current_process.get(field) == origin_process.get(field) for field in identity_fields):
            return False
        return True
    if current_session != payload.get("origin_session_digest"):
        return True
    if origin_process is None and current_process is not None:
        try:
            return float(current_process["started_at_epoch"]) > restart_boundary(
                payload
            ).timestamp()
        except (KeyError, TypeError, ValueError, TransactionError):
            return False
    return False


def restart_boundary(payload: dict[str, Any]) -> datetime:
    """Return the latest recorded boundary before a mandatory host restart."""
    for field in (
        "install_finished_at",
        "install_started_at",
        "refresh_finished_at",
        "refresh_started_at",
    ):
        if payload.get(field) is not None:
            return parse_timestamp(payload[field])
    raise TransactionError("transaction has no restart boundary")


def run_command(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 30,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TransactionError(f"command could not complete: {arguments[0]}") from exc
    if len(result.stdout.encode("utf-8")) > MAX_CAPTURE_BYTES:
        raise TransactionError(f"command output exceeded limit: {arguments[0]}")
    if len(result.stderr.encode("utf-8")) > MAX_CAPTURE_BYTES:
        raise TransactionError(f"command diagnostics exceeded limit: {arguments[0]}")
    if check and result.returncode != 0:
        raise TransactionError(f"command failed with exit {result.returncode}: {arguments[0]}")
    return result


def parse_json_output(result: subprocess.CompletedProcess[str], label: str) -> dict[str, Any]:
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise TransactionError(f"{label} did not return JSON") from exc
    if not isinstance(value, dict):
        raise TransactionError(f"{label} returned an unsupported JSON shape")
    return value


def parse_json_array_output(
    result: subprocess.CompletedProcess[str], label: str
) -> list[dict[str, Any]]:
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise TransactionError(f"{label} did not return JSON") from exc
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise TransactionError(f"{label} returned an unsupported JSON shape")
    return value


def git_snapshot(root: Path, label: str, *, require_clean: bool) -> dict[str, Any]:
    if not (root / ".git").exists():
        raise TransactionError(f"{label} is not a Git worktree: {root}")
    head = run_command(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    status = run_command(
        ["git", "status", "--porcelain=v2", "--untracked-files=all"], cwd=root
    ).stdout
    if require_clean and status:
        raise TransactionError(f"{label} Git worktree must be clean")
    return {
        "head": head,
        "status_digest": digest_text(status),
        "clean": not bool(status),
    }


def task_snapshot(project_root: Path) -> dict[str, str]:
    script = project_root / ".trellis" / "scripts" / "task.py"
    if not script.is_file():
        raise TransactionError("project has no Trellis task.py")
    result = run_command([sys.executable, str(script), "current", "--json"], cwd=project_root)
    payload = parse_json_output(result, "Trellis task query")
    task = payload.get("current_task")
    if not isinstance(task, dict):
        raise TransactionError("project has no current Trellis task")
    snapshot: dict[str, str] = {}
    for field in ("dir", "id", "status"):
        value = task.get(field)
        if not isinstance(value, str) or not value:
            raise TransactionError(f"current Trellis task has no {field}")
        snapshot[field] = value
    return snapshot


def plugin_list() -> list[dict[str, Any]]:
    result = run_command(["codex", "plugin", "list", "--json"], timeout=60)
    payload = parse_json_output(result, "codex plugin list")
    installed = payload.get("installed")
    if not isinstance(installed, list):
        raise TransactionError("codex plugin list has no installed array")
    return [item for item in installed if isinstance(item, dict)]


def installed_plugin(selector: str) -> dict[str, Any]:
    for item in plugin_list():
        if item.get("pluginId") == selector:
            if item.get("installed") is not True or item.get("enabled") is not True:
                raise TransactionError(f"plugin is not installed and enabled: {selector}")
            version = item.get("version")
            if not isinstance(version, str) or not version:
                raise TransactionError(f"plugin has no installed version: {selector}")
            return {
                "plugin_id": selector,
                "version": version,
                "enabled": True,
            }
    raise TransactionError(f"plugin is not installed: {selector}")


def marketplace_snapshot(name: str) -> dict[str, Any]:
    result = run_command(["codex", "plugin", "marketplace", "list", "--json"], timeout=60)
    payload = parse_json_output(result, "codex plugin marketplace list")
    entries = payload.get("marketplaces")
    if not isinstance(entries, list):
        raise TransactionError("codex plugin marketplace list has no marketplaces array")
    matches = [
        item for item in entries if isinstance(item, dict) and item.get("name") == name
    ]
    if len(matches) != 1:
        raise TransactionError(f"marketplace is not uniquely configured: {name}")
    item = matches[0]
    root_value = item.get("root")
    if not isinstance(root_value, str) or not root_value:
        raise TransactionError(f"marketplace has no root: {name}")
    marketplace_root = Path(root_value).expanduser().resolve()
    if not marketplace_root.is_dir():
        raise TransactionError(f"marketplace root is not a directory: {name}")

    source = item.get("marketplaceSource")
    if source is None:
        source_type = "builtin"
        source_digest = None
    elif isinstance(source, dict):
        source_type = source.get("sourceType")
        source_value = source.get("source")
        if source_type not in {"git", "local"}:
            raise TransactionError(f"marketplace source type is unsupported: {name}")
        if not isinstance(source_value, str) or not source_value:
            raise TransactionError(f"marketplace source is missing: {name}")
        source_digest = digest_text(source_value)
    else:
        raise TransactionError(f"marketplace source is invalid: {name}")

    revision = None
    if source_type == "git":
        revision = run_command(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=marketplace_root
        ).stdout.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", revision):
            raise TransactionError(f"marketplace Git revision is invalid: {name}")

    return {
        "name": name,
        "root": str(marketplace_root),
        "source_type": source_type,
        "source_digest": source_digest,
        "revision": revision,
        "refresh_required": source_type == "git",
    }


def marketplace_source_matches(first: dict[str, Any], second: dict[str, Any]) -> bool:
    fields = ("name", "root", "source_type", "source_digest", "refresh_required")
    return all(first.get(field) == second.get(field) for field in fields)


def marketplace_snapshot_matches(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return marketplace_source_matches(first, second) and first.get("revision") == second.get(
        "revision"
    )


def plugin_cache_path(root: Path, plugin_name: str, marketplace: str, version: str) -> Path:
    cache_root = root / "plugins" / "cache" / marketplace / plugin_name / version
    plugin_root = root / "plugins"
    if (
        cache_root.is_symlink()
        or (cache_root.exists() and cache_root.resolve() != cache_root)
        or not cache_root.is_relative_to(plugin_root)
    ):
        raise TransactionError("installed plugin cache contains a symbolic path")
    return cache_root


def plugin_mcp_declarations(
    root: Path, plugin_name: str, marketplace: str, version: str
) -> list[dict[str, str]]:
    cache_root = plugin_cache_path(root, plugin_name, marketplace, version)
    manifest = cache_root / ".codex-plugin" / "mcp.json"
    if not manifest.exists():
        return []
    if manifest.is_symlink() or not manifest.is_file() or manifest.resolve() != manifest:
        raise TransactionError("installed Plugin MCP manifest contains a symbolic path")
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TransactionError("installed Plugin MCP manifest is invalid") from exc
    servers = payload.get("mcpServers") if isinstance(payload, dict) else None
    if not isinstance(servers, dict) or not servers:
        raise TransactionError("installed Plugin MCP manifest has no mcpServers object")

    declarations: list[dict[str, str]] = []
    for server_name, config in servers.items():
        if not isinstance(server_name, str) or not server_name or not isinstance(config, dict):
            raise TransactionError("installed Plugin MCP declaration is invalid")
        command = config.get("command")
        cwd_value = config.get("cwd", ".")
        if not isinstance(command, str) or not command or not isinstance(cwd_value, str):
            raise TransactionError(f"Plugin MCP declaration is incomplete: {server_name}")
        command_basename = Path(command).name
        if not command_basename:
            raise TransactionError(f"Plugin MCP command is invalid: {server_name}")
        declared_path = Path(cwd_value).expanduser()
        if not declared_path.is_absolute():
            declared_path = cache_root / declared_path
        declared_path = declared_path.resolve()
        if not declared_path.is_dir() or not declared_path.is_relative_to(cache_root):
            raise TransactionError(
                f"Plugin MCP cwd is not a stable installed cache directory: {server_name}"
            )
        declarations.append(
            {
                "name": server_name,
                "command_basename": command_basename,
                "declared_cwd": str(declared_path),
                "plugin_family_root": str(cache_root.parent),
            }
        )
    declarations.sort(key=lambda item: item["name"])
    return declarations


def mcp_inventory() -> list[dict[str, Any]]:
    result = run_command(["codex", "mcp", "list", "--json"], timeout=60)
    return parse_json_array_output(result, "codex mcp list")


def configured_mcp_contracts(
    declarations: list[dict[str, str]], inventory: list[dict[str, Any]]
) -> list[dict[str, str]]:
    contracts: list[dict[str, str]] = []
    for declaration in declarations:
        matches = [item for item in inventory if item.get("name") == declaration["name"]]
        if len(matches) != 1:
            raise TransactionError(
                f"Codex MCP inventory does not uniquely contain {declaration['name']}"
            )
        item = matches[0]
        transport = item.get("transport")
        if item.get("enabled") is not True or not isinstance(transport, dict):
            raise TransactionError(f"Codex MCP is not enabled: {declaration['name']}")
        if transport.get("type") != "stdio":
            raise TransactionError(f"Plugin MCP transport is not stdio: {declaration['name']}")
        command = transport.get("command")
        cwd_value = transport.get("cwd")
        if not isinstance(command, str) or not isinstance(cwd_value, str):
            raise TransactionError(
                f"Codex MCP inventory lacks command or cwd: {declaration['name']}"
            )
        command_basename = Path(command).name
        declared_cwd = str(Path(cwd_value).expanduser().resolve())
        if command_basename != declaration["command_basename"]:
            raise TransactionError(f"Codex MCP command differs from manifest: {declaration['name']}")
        if declared_cwd != declaration["declared_cwd"]:
            raise TransactionError(f"Codex MCP cwd differs from manifest: {declaration['name']}")
        contracts.append(dict(declaration))
    return contracts


def proc_descendants(proc_root: Path, ancestor_pid: int) -> list[dict[str, Any]]:
    parents: dict[int, int] = {}
    commands: dict[int, str] = {}
    try:
        entries = list(proc_root.iterdir())
    except OSError as exc:
        raise TransactionError("Linux process table is unavailable") from exc
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            stat_text = (entry / "stat").read_text(encoding="utf-8")
            closing = stat_text.rfind(")")
            if closing < 0:
                continue
            fields = stat_text[closing + 2 :].split()
            if len(fields) < 20:
                continue
            pid = int(entry.name)
            parents[pid] = int(fields[1])
            commands[pid] = (entry / "comm").read_text(encoding="utf-8").strip()
        except (OSError, ValueError, IndexError):
            continue

    def descends_from(pid: int) -> bool:
        seen: set[int] = set()
        current = pid
        while current > 1 and current not in seen:
            seen.add(current)
            parent = parents.get(current)
            if parent is None:
                return False
            if parent == ancestor_pid:
                return True
            current = parent
        return False

    descendants: list[dict[str, Any]] = []
    for pid in sorted(parents):
        if not descends_from(pid):
            continue
        try:
            cwd = os.readlink(proc_root / str(pid) / "cwd")
            executable = os.readlink(proc_root / str(pid) / "exe")
        except OSError:
            continue
        descendants.append(
            {
                "pid": pid,
                "comm": commands[pid],
                "cwd": cwd,
                "executable_basename": Path(executable.removesuffix(" (deleted)")).name,
            }
        )
    return descendants


def is_matching_deleted_backup_cwd(actual_cwd: str, contract: dict[str, str]) -> bool:
    """Accept only Codex's current-release, unlinked backup layout."""
    if not actual_cwd.endswith(" (deleted)"):
        return False
    actual = Path(actual_cwd.removesuffix(" (deleted)"))
    declared = Path(contract["declared_cwd"])
    family_root = Path(contract["plugin_family_root"])
    if declared.parent != family_root:
        return False
    if actual.name != declared.name or actual.parent.name != family_root.name:
        return False
    backup_root = actual.parent.parent
    return (
        backup_root.parent == family_root.parent
        and re.fullmatch(r"plugin-backup-[A-Za-z0-9]+", backup_root.name) is not None
    )


def verify_mcp_processes(
    contracts: list[dict[str, str]],
    proc_root: Path,
    codex_pid: int,
    *,
    allow_matching_deleted_backup: bool = False,
) -> list[dict[str, str]]:
    processes = proc_descendants(proc_root, codex_pid)
    verified: list[dict[str, str]] = []
    claimed_pids: set[int] = set()
    for contract in contracts:
        command = contract["command_basename"]
        declared_cwd = contract["declared_cwd"]
        family_root = Path(contract["plugin_family_root"])
        command_matches = [
            process
            for process in processes
            if process["executable_basename"] == command
        ]
        exact = [
            process
            for process in command_matches
            if process["cwd"].removesuffix(" (deleted)") == declared_cwd
        ]
        if len(exact) != 1:
            related = []
            for process in command_matches:
                actual = process["cwd"].removesuffix(" (deleted)")
                try:
                    in_family = Path(actual).is_relative_to(family_root)
                except ValueError:
                    in_family = False
                if in_family or "plugin-backup-" in actual:
                    related.append(process)
            if len(exact) == 0 and len(related) == 1:
                process = related[0]
                actual = process["cwd"]
                if (
                    allow_matching_deleted_backup
                    and is_matching_deleted_backup_cwd(actual, contract)
                ):
                    if process["pid"] in claimed_pids:
                        raise TransactionError(
                            f"Plugin MCP process is shared across declarations: {contract['name']}"
                        )
                    claimed_pids.add(process["pid"])
                    verified.append(
                        {
                            "name": contract["name"],
                            "command_basename": command,
                            "declared_cwd": declared_cwd,
                            "runtime_cwd_kind": "current_release_deleted_backup",
                        }
                    )
                    continue
                if actual.endswith(" (deleted)"):
                    raise TransactionError(
                        f"Plugin MCP cwd is deleted: {contract['name']}"
                    )
                raise TransactionError(
                    f"Plugin MCP cwd does not match installed version: {contract['name']}"
                )
            raise TransactionError(
                f"Plugin MCP process is not uniquely identifiable: {contract['name']}"
            )
        process = exact[0]
        if process["pid"] in claimed_pids:
            raise TransactionError(
                f"Plugin MCP process is shared across declarations: {contract['name']}"
            )
        claimed_pids.add(process["pid"])
        actual_cwd = process["cwd"]
        if actual_cwd.endswith(" (deleted)"):
            raise TransactionError(f"Plugin MCP cwd is deleted: {contract['name']}")
        if "plugin-backup-" in actual_cwd:
            raise TransactionError(f"Plugin MCP cwd uses a backup directory: {contract['name']}")
        if not Path(actual_cwd).is_dir():
            raise TransactionError(f"Plugin MCP cwd does not exist: {contract['name']}")
        verified.append(
            {
                "name": contract["name"],
                "command_basename": command,
                "declared_cwd": declared_cwd,
                "actual_cwd": actual_cwd,
            }
        )
    verified.sort(key=lambda item: item["name"])
    return verified


def mcp_runtime_snapshot(
    root: Path,
    plugin_name: str,
    marketplace: str,
    version: str,
    *,
    proc_root: Path = Path("/proc"),
    codex_pid: int | None = None,
    inventory: list[dict[str, Any]] | None = None,
    allow_deleted_cwd: bool = False,
    allow_matching_deleted_backup: bool = False,
) -> dict[str, Any]:
    declarations = plugin_mcp_declarations(root, plugin_name, marketplace, version)
    if not declarations:
        return {"status": "not_applicable", "count": 0, "servers": []}
    if sys.platform != "linux":
        raise TransactionError("Plugin MCP process verification requires Linux/WSL")
    contracts = configured_mcp_contracts(
        declarations, inventory if inventory is not None else mcp_inventory()
    )
    if codex_pid is None:
        identity = codex_process_identity()
        if identity is None:
            raise TransactionError("current Codex process is not identifiable")
        codex_pid = int(identity["pid"])
    try:
        servers = verify_mcp_processes(
            contracts,
            proc_root,
            codex_pid,
            allow_matching_deleted_backup=allow_matching_deleted_backup,
        )
    except TransactionError as exc:
        # A deleted cwd is the one recoverable pre-update baseline: install must
        # still replace the Plugin and recover must prove a live stable cwd.
        if not allow_deleted_cwd or not str(exc).startswith("Plugin MCP cwd is deleted:"):
            raise
        return {
            "status": "degraded",
            "count": len(contracts),
            "servers": [],
            "degraded_reason": "deleted_cwd",
        }
    return {"status": "verified", "count": len(servers), "servers": servers}


def app_server_request(
    process: subprocess.Popen[str],
    io_selector: selectors.BaseSelector,
    request_id: int,
    method: str,
    params: dict[str, Any],
    deadline: float,
) -> dict[str, Any]:
    if process.stdin is None or process.stdout is None:
        raise TransactionError("Codex app-server stdio is unavailable")
    process.stdin.write(
        json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        + "\n"
    )
    process.stdin.flush()
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not io_selector.select(remaining):
            raise TransactionError(f"Codex app-server timed out during {method}")
        line = process.stdout.readline()
        if not line:
            raise TransactionError(f"Codex app-server exited during {method}")
        if len(line.encode("utf-8")) > MAX_CAPTURE_BYTES:
            raise TransactionError("Codex app-server response exceeded limit")
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict) or message.get("id") != request_id:
            continue
        if message.get("error") is not None:
            raise TransactionError(f"Codex app-server rejected {method}")
        result = message.get("result")
        if not isinstance(result, dict):
            raise TransactionError(f"Codex app-server returned invalid {method} result")
        return result


def runtime_hook_snapshot(
    project_root: Path,
    plugin_selector: str,
    *,
    require_trusted: bool = True,
) -> dict[str, Any]:
    try:
        process = subprocess.Popen(
            ["codex", "app-server", "--stdio"],
            cwd=project_root,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1,
        )
    except OSError as exc:
        raise TransactionError("Codex app-server could not start") from exc
    io_selector = selectors.DefaultSelector()
    try:
        if process.stdout is None or process.stdin is None:
            raise TransactionError("Codex app-server stdio is unavailable")
        io_selector.register(process.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + APP_SERVER_TIMEOUT_SECONDS
        app_server_request(
            process,
            io_selector,
            1,
            "initialize",
            {
                "clientInfo": {
                    "name": "codex-plugin-update",
                    "title": "Codex Plugin Update Transaction",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "experimentalApi": True,
                    "optOutNotificationMethods": ["item/agentMessage/delta"],
                },
            },
            deadline,
        )
        process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "initialized", "params": {}}) + "\n"
        )
        process.stdin.flush()
        response = app_server_request(
            process,
            io_selector,
            2,
            "hooks/list",
            {"cwds": [str(project_root)]},
            deadline,
        )
    finally:
        io_selector.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
    entries = response.get("data")
    if not isinstance(entries, list):
        raise TransactionError("Codex hooks/list has no data array")
    hooks: list[dict[str, Any]] = []
    for entry in entries:
        entry_hooks = entry.get("hooks") if isinstance(entry, dict) else None
        if not isinstance(entry_hooks, list):
            continue
        for hook in entry_hooks:
            if not isinstance(hook, dict) or hook.get("pluginId") != plugin_selector:
                continue
            current_hash = hook.get("currentHash")
            hooks.append(
                {
                    "event_name": hook.get("eventName"),
                    "enabled": hook.get("enabled"),
                    "trust_status": hook.get("trustStatus"),
                    "current_hash": current_hash if isinstance(current_hash, str) else None,
                }
            )
    hooks.sort(key=lambda item: json.dumps(item, sort_keys=True))
    if not hooks:
        raise TransactionError(f"Codex app-server did not load hooks for {plugin_selector}")
    if any(item["enabled"] is not True for item in hooks):
        raise TransactionError(f"Codex app-server reports disabled hooks for {plugin_selector}")
    allowed_trust = {"trusted"} if require_trusted else {"trusted", "untrusted"}
    if any(item["trust_status"] not in allowed_trust for item in hooks):
        raise TransactionError(f"Codex app-server reports untrusted hooks for {plugin_selector}")
    if any(
        not isinstance(item["current_hash"], str)
        or not SHA256_DIGEST.fullmatch(item["current_hash"])
        for item in hooks
    ):
        raise TransactionError(
            f"Codex app-server reports invalid hook hashes for {plugin_selector}"
        )
    return {"plugin_id": plugin_selector, "count": len(hooks), "hooks": hooks}


def hook_snapshot(root: Path, plugin_name: str, marketplace: str, version: str) -> dict[str, Any]:
    cache_root = plugin_cache_path(root, plugin_name, marketplace, version)
    hooks = (
        sorted(path for path in cache_root.rglob("hooks.json") if path.is_file())
        if cache_root.is_dir()
        else []
    )
    if not hooks:
        raise TransactionError(
            f"installed cache has no hooks.json for {plugin_name}@{marketplace} {version}"
        )
    if any(path.is_symlink() or path.resolve() != path for path in hooks):
        raise TransactionError("installed plugin Hook manifest contains a symbolic path")
    return {
        "version": version,
        "cache_path": cache_root.relative_to(root).as_posix(),
        "hooks": [
            {
                "path": path.relative_to(root).as_posix(),
                "digest": file_digest(path),
            }
            for path in hooks
        ],
    }


def environment_snapshot(
    root: Path,
    project_root: Path,
    selector: str,
    *,
    allow_degraded_mcp: bool = False,
) -> dict[str, Any]:
    plugin_name, marketplace = parse_selector(selector)
    plugin = installed_plugin(selector)
    return {
        # Project edits may be legitimately in flight. Capture the exact status
        # and require it to remain unchanged through install/recovery instead of
        # forcing an unrelated commit solely to update a global Plugin.
        "project_git": git_snapshot(project_root, "project", require_clean=False),
        "codex_git": git_snapshot(root, "CODEX_HOME", require_clean=True),
        "task": task_snapshot(project_root),
        "plugin": plugin,
        "marketplace": marketplace_snapshot(marketplace),
        "hook": hook_snapshot(root, plugin_name, marketplace, plugin["version"]),
        "runtime_hook": runtime_hook_snapshot(
            project_root, selector, require_trusted=False
        ),
        "mcp": mcp_runtime_snapshot(
            root,
            plugin_name,
            marketplace,
            plugin["version"],
            allow_deleted_cwd=allow_degraded_mcp,
        ),
    }


def codex_recovery_tool_update_allowed(
    root: Path,
    expected: dict[str, Any],
    current: dict[str, Any],
) -> bool:
    if expected.get("clean") is not True or current.get("clean") is not True:
        return False
    old_head = expected.get("head")
    new_head = current.get("head")
    if not isinstance(old_head, str) or not isinstance(new_head, str) or old_head == new_head:
        return False
    ancestry = run_command(
        ["git", "merge-base", "--is-ancestor", old_head, new_head],
        cwd=root,
        check=False,
    )
    if ancestry.returncode != 0:
        return False
    changed = run_command(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", old_head, new_head],
        cwd=root,
    ).stdout.splitlines()
    return bool(changed) and set(changed) <= RECOVERY_TOOL_UPDATE_PATHS


def compare_snapshot(
    root: Path,
    project_root: Path,
    expected: dict[str, Any],
    *,
    allow_codex_recovery_tool_update: bool = False,
) -> list[str]:
    errors: list[str] = []
    try:
        project_git = git_snapshot(project_root, "project", require_clean=False)
        if project_git != expected.get("project_git"):
            errors.append("project Git snapshot changed")
    except TransactionError as exc:
        errors.append(str(exc))
    try:
        codex_git = git_snapshot(root, "CODEX_HOME", require_clean=False)
        expected_codex_git = expected.get("codex_git")
        recovery_update_allowed = (
            allow_codex_recovery_tool_update
            and isinstance(expected_codex_git, dict)
            and codex_recovery_tool_update_allowed(root, expected_codex_git, codex_git)
        )
        if codex_git != expected_codex_git and not recovery_update_allowed:
            errors.append("CODEX_HOME Git snapshot changed")
    except TransactionError as exc:
        errors.append(str(exc))
    try:
        if task_snapshot(project_root) != expected.get("task"):
            errors.append("current Trellis task changed")
    except TransactionError as exc:
        errors.append(str(exc))
    return errors


def transaction_path(root: Path, transaction_id: str) -> Path:
    if not TRANSACTION_ID.fullmatch(transaction_id):
        raise TransactionError("transaction id is invalid")
    directory = root / transaction_id
    if directory.exists() and (
        directory.is_symlink() or not directory.is_dir() or directory.resolve() != directory
    ):
        raise TransactionError("transaction directory is unsafe")
    return directory / "transaction.json"


def load_transaction(root: Path, transaction_id: str) -> tuple[Path, dict[str, Any]]:
    path = transaction_path(root, transaction_id)
    if path.is_symlink():
        raise TransactionError(f"transaction file is a symbolic link: {transaction_id}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TransactionError(f"transaction does not exist: {transaction_id}") from exc
    except json.JSONDecodeError as exc:
        raise TransactionError(f"transaction is invalid: {transaction_id}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise TransactionError(f"transaction schema is unsupported: {transaction_id}")
    if payload.get("id") != transaction_id:
        raise TransactionError(f"transaction id does not match its path: {transaction_id}")
    validate_transaction_payload(payload)
    return path, payload


def validate_transaction_payload(payload: dict[str, Any]) -> None:
    if payload.get("state") not in TRANSACTION_STATES:
        raise TransactionError("transaction state is unsupported")
    parse_timestamp(payload.get("created_at"))
    parse_timestamp(payload.get("expires_at"))
    plugin = payload.get("plugin")
    if not isinstance(plugin, dict):
        raise TransactionError("transaction plugin metadata is missing")
    selector = plugin.get("selector")
    if not isinstance(selector, str):
        raise TransactionError("transaction plugin selector is missing")
    plugin_name, marketplace = parse_selector(selector)
    if plugin.get("name") != plugin_name or plugin.get("marketplace") != marketplace:
        raise TransactionError("transaction plugin selector metadata is inconsistent")
    for field in ("from_version", "target_version"):
        value = plugin.get(field)
        if not isinstance(value, str):
            raise TransactionError(f"transaction plugin {field} is missing")
        validate_version(value)
    project_root = payload.get("project_root")
    if not isinstance(project_root, str) or not Path(project_root).is_absolute():
        raise TransactionError("transaction project root is invalid")
    origin = payload.get("origin_session_digest")
    if not isinstance(origin, str) or not SHA256_DIGEST.fullmatch(origin):
        raise TransactionError("transaction origin session digest is invalid")
    snapshot = payload.get("snapshot")
    if not isinstance(snapshot, dict):
        raise TransactionError("transaction environment snapshot is missing")
    for field in (
        "project_git",
        "codex_git",
        "task",
        "plugin",
        "marketplace",
        "hook",
        "runtime_hook",
        "mcp",
    ):
        if not isinstance(snapshot.get(field), dict):
            raise TransactionError(f"transaction snapshot {field} is missing")


def resolve_transaction_id(root: Path, value: str) -> str:
    if value != "latest":
        if not TRANSACTION_ID.fullmatch(value):
            raise TransactionError("transaction id is invalid")
        return value
    candidates: list[tuple[str, str]] = []
    if root.is_dir():
        for path in root.glob("*/transaction.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and payload.get("state") in ACTIVE_TRANSACTION_STATES:
                transaction_id = payload.get("id")
                created_at = payload.get("created_at")
                if isinstance(transaction_id, str) and isinstance(created_at, str):
                    candidates.append((created_at, transaction_id))
    if not candidates:
        raise TransactionError("no active plugin update transaction exists")
    if len(candidates) != 1:
        raise TransactionError("multiple active transactions exist; use an exact id")
    return candidates[0][1]


def unexpired_active_transactions(root: Path) -> list[str]:
    active: list[str] = []
    if not root.is_dir():
        return active
    now = utc_now()
    for path in root.glob("*/transaction.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            state = payload.get("state") if isinstance(payload, dict) else None
            expires = (
                parse_timestamp(payload.get("expires_at"))
                if isinstance(payload, dict)
                else now
            )
            transaction_id = payload.get("id") if isinstance(payload, dict) else None
        except (OSError, json.JSONDecodeError, TransactionError):
            active.append(path.parent.name)
            continue
        if state in ACTIVE_TRANSACTION_STATES and isinstance(transaction_id, str):
            if state != "prepared" or expires > now:
                active.append(transaction_id)
    return sorted(active)


def require_project_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise TransactionError(f"project root is not a directory: {root}")
    return root


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    root = code_home()
    project_root = require_project_root(args.project_root)
    plugin_name, marketplace = parse_selector(args.plugin)
    target_version = validate_version(args.target_version)
    state_root = transaction_root(root)
    with transaction_lock(state_root):
        active = unexpired_active_transactions(state_root)
        if active:
            raise TransactionError(f"another plugin update transaction is active: {active[0]}")
        snapshot = environment_snapshot(
            root,
            project_root,
            args.plugin,
            allow_degraded_mcp=True,
        )
        if snapshot["plugin"]["version"] == target_version:
            raise TransactionError("target version is already installed")
        transaction_id = secrets.token_hex(16)
        created = utc_now()
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "id": transaction_id,
            "state": "prepared",
            "created_at": timestamp(created),
            "expires_at": timestamp(created + timedelta(minutes=args.ttl_minutes)),
            "plugin": {
                "selector": args.plugin,
                "name": plugin_name,
                "marketplace": marketplace,
                "from_version": snapshot["plugin"]["version"],
                "target_version": target_version,
            },
            "project_root": str(project_root),
            "origin_session_digest": session_digest(),
            "snapshot": snapshot,
        }
        origin_process = codex_process_identity()
        if origin_process is not None:
            payload["origin_process"] = origin_process
        path = transaction_path(state_root, transaction_id)
        atomic_json_write(path, payload)
    return {
        "transaction_id": transaction_id,
        "state": "prepared",
        "plugin": args.plugin,
        "from_version": snapshot["plugin"]["version"],
        "target_version": target_version,
        "expires_at": payload["expires_at"],
        "next": f"plugin-update-transaction.py install --transaction {transaction_id}",
    }


def verify_origin_environment(root: Path, payload: dict[str, Any]) -> None:
    origin_process = payload.get("origin_process")
    current_process = codex_process_identity()
    if isinstance(origin_process, dict) and current_process is not None:
        identity_fields = ("boot_id_digest", "pid", "start_ticks")
        if any(current_process.get(field) != origin_process.get(field) for field in identity_fields):
            raise TransactionError("install must run in the Codex process that prepared the transaction")
    elif payload.get("origin_session_digest") != session_digest():
        raise TransactionError("install must run in the session that prepared the transaction")
    project_root = require_project_root(str(payload.get("project_root", "")))
    errors = compare_snapshot(root, project_root, payload.get("snapshot", {}))
    if errors:
        raise TransactionError("pre-install checks failed: " + "; ".join(errors))
    plugin = installed_plugin(payload["plugin"]["selector"])
    if plugin["version"] != payload["plugin"]["from_version"]:
        raise TransactionError("installed plugin version changed after prepare")
    hook = hook_snapshot(
        root,
        payload["plugin"]["name"],
        payload["plugin"]["marketplace"],
        plugin["version"],
    )
    if hook != payload["snapshot"]["hook"]:
        raise TransactionError("installed plugin Hook files changed after prepare")
    runtime_hook = runtime_hook_snapshot(
        project_root,
        payload["plugin"]["selector"],
        require_trusted=False,
    )
    if runtime_hook != payload["snapshot"]["runtime_hook"]:
        raise TransactionError("Codex runtime Hook state changed after prepare")
    current_marketplace = marketplace_snapshot(payload["plugin"]["marketplace"])
    if not marketplace_snapshot_matches(
        current_marketplace, payload["snapshot"]["marketplace"]
    ):
        raise TransactionError("marketplace snapshot changed after prepare")
    expected_mcp = payload["snapshot"]["mcp"]
    allow_deleted_cwd = (
        expected_mcp.get("status") == "degraded"
        and expected_mcp.get("degraded_reason") == "deleted_cwd"
    )
    current_mcp = mcp_runtime_snapshot(
        root,
        payload["plugin"]["name"],
        payload["plugin"]["marketplace"],
        plugin["version"],
        allow_deleted_cwd=allow_deleted_cwd,
    )
    if current_mcp != expected_mcp:
        raise TransactionError("Plugin MCP runtime changed after prepare")


def install(args: argparse.Namespace) -> dict[str, Any]:
    root = code_home()
    state_root = transaction_root(root)
    transaction_id = resolve_transaction_id(state_root, args.transaction)
    with transaction_lock(state_root):
        path, payload = load_transaction(state_root, transaction_id)
        if payload.get("state") != "prepared":
            raise TransactionError(f"transaction is not prepared: {payload.get('state')}")
        if parse_timestamp(payload.get("expires_at")) <= utc_now():
            payload["state"] = "expired"
            payload["expired_at"] = timestamp()
            atomic_json_write(path, payload)
            raise TransactionError("transaction expired before install")
        verify_origin_environment(root, payload)
        selector = payload["plugin"]["selector"]
        marketplace_before = payload["snapshot"]["marketplace"]
        if marketplace_before["refresh_required"]:
            marketplace_name = payload["plugin"]["marketplace"]
            payload["state"] = "refreshing"
            payload["refresh_started_at"] = timestamp()
            atomic_json_write(path, payload)
            try:
                refresh_result = run_command(
                    [
                        "codex",
                        "plugin",
                        "marketplace",
                        "upgrade",
                        marketplace_name,
                        "--json",
                    ],
                    timeout=args.timeout_seconds,
                    check=False,
                )
            except TransactionError as exc:
                payload["state"] = "refresh_failed"
                payload["refresh_finished_at"] = timestamp()
                payload["failure"] = {
                    "kind": "marketplace_upgrade_execution_error",
                    "message": str(exc),
                }
                atomic_json_write(path, payload)
                raise TransactionError(
                    f"marketplace refresh ended without a reliable result; restart Codex now, "
                    f"then recover transaction {transaction_id}"
                ) from exc
            if refresh_result.returncode != 0:
                payload["state"] = "refresh_failed"
                payload["refresh_finished_at"] = timestamp()
                payload["failure"] = {
                    "kind": "marketplace_upgrade_failed",
                    "exit_code": refresh_result.returncode,
                }
                atomic_json_write(path, payload)
                raise TransactionError(
                    f"marketplace refresh failed with exit {refresh_result.returncode}; "
                    f"restart Codex now, then recover transaction {transaction_id}"
                )
            try:
                parse_json_output(refresh_result, "codex plugin marketplace upgrade")
                marketplace_after = marketplace_snapshot(marketplace_name)
                if not marketplace_source_matches(marketplace_before, marketplace_after):
                    raise TransactionError("marketplace source identity changed during refresh")
            except TransactionError as exc:
                payload["state"] = "recovery_required"
                payload["refresh_finished_at"] = timestamp()
                payload["failure"] = {
                    "kind": "marketplace_refresh_verification_failed",
                    "message": str(exc),
                }
                atomic_json_write(path, payload)
                raise TransactionError(
                    f"marketplace refresh could not be verified; restart Codex now, "
                    f"then recover transaction {transaction_id}"
                ) from exc
            payload["refresh_finished_at"] = timestamp()
            payload["marketplace_after_refresh"] = marketplace_after
        else:
            payload["marketplace_after_refresh"] = marketplace_before
        payload["state"] = "installing"
        payload["install_started_at"] = timestamp()
        atomic_json_write(path, payload)
        try:
            result = run_command(
                ["codex", "plugin", "add", selector, "--json"],
                timeout=args.timeout_seconds,
                check=False,
            )
        except TransactionError as exc:
            payload["state"] = "install_failed"
            payload["install_finished_at"] = timestamp()
            payload["failure"] = {
                "kind": "plugin_add_execution_error",
                "message": str(exc),
            }
            atomic_json_write(path, payload)
            raise TransactionError(
                f"codex plugin add ended without a reliable result; restart Codex now, "
                f"then recover transaction {transaction_id}"
            ) from exc
        if result.returncode != 0:
            payload["state"] = "install_failed"
            payload["install_finished_at"] = timestamp()
            payload["failure"] = {"kind": "plugin_add_failed", "exit_code": result.returncode}
            atomic_json_write(path, payload)
            raise TransactionError(
                f"codex plugin add failed with exit {result.returncode}; restart Codex now, "
                f"then recover transaction {transaction_id}"
            )
        try:
            plugin = installed_plugin(selector)
            target = payload["plugin"]["target_version"]
            if plugin["version"] != target:
                raise TransactionError(
                    f"installed version {plugin['version']} does not match target {target}"
                )
            hook = hook_snapshot(
                root,
                payload["plugin"]["name"],
                payload["plugin"]["marketplace"],
                target,
            )
            runtime_hook = runtime_hook_snapshot(
                require_project_root(str(payload["project_root"])), selector
            )
        except TransactionError as exc:
            payload["state"] = "recovery_required"
            payload["install_finished_at"] = timestamp()
            payload["failure"] = {"kind": "post_install_verification_failed", "message": str(exc)}
            atomic_json_write(path, payload)
            raise TransactionError(
                f"post-install verification failed; restart Codex now, then recover "
                f"transaction {transaction_id}"
            ) from exc
        payload["state"] = "restart_required"
        payload["install_finished_at"] = timestamp()
        payload["installed"] = {
            "plugin": plugin,
            "marketplace": payload["marketplace_after_refresh"],
            "hook": hook,
            "runtime_hook": runtime_hook,
        }
        payload.pop("failure", None)
        atomic_json_write(path, payload)
    return {
        "transaction_id": transaction_id,
        "state": "restart_required",
        "plugin": selector,
        "installed_version": plugin["version"],
        "action_required": "restart_codex_now",
        "recover": f"plugin-update-transaction.py recover --transaction {transaction_id}",
    }


def recover(args: argparse.Namespace) -> dict[str, Any]:
    root = code_home()
    state_root = transaction_root(root)
    transaction_id = resolve_transaction_id(state_root, args.transaction)
    with transaction_lock(state_root):
        path, payload = load_transaction(state_root, transaction_id)
        state = payload.get("state")
        if state not in {
            "restart_required",
            "recovery_required",
            "refreshing",
            "refresh_failed",
            "installing",
            "install_failed",
        }:
            raise TransactionError(f"transaction cannot be recovered from state: {state}")
        current_session = session_digest()
        current_process = codex_process_identity()
        if not restart_proven(payload, current_session, current_process):
            raise TransactionError(
                "recover requires a newly started Codex process; CODEX_THREAD_ID may remain stable "
                "when the same conversation is resumed"
            )
        project_root = require_project_root(str(payload.get("project_root", "")))
        if args.project_root and require_project_root(args.project_root) != project_root:
            raise TransactionError("provided project root does not match the transaction")
        errors = compare_snapshot(
            root,
            project_root,
            payload.get("snapshot", {}),
            allow_codex_recovery_tool_update=True,
        )
        selector = payload["plugin"]["selector"]
        target = payload["plugin"]["target_version"]
        plugin: dict[str, Any] | None = None
        hook: dict[str, Any] | None = None
        runtime_hook: dict[str, Any] | None = None
        mcp: dict[str, Any] | None = None
        current_marketplace: dict[str, Any] | None = None
        try:
            current_marketplace = marketplace_snapshot(payload["plugin"]["marketplace"])
            if not marketplace_source_matches(
                payload["snapshot"]["marketplace"], current_marketplace
            ):
                errors.append("marketplace source identity changed")
        except TransactionError as exc:
            errors.append(str(exc))
        try:
            plugin = installed_plugin(selector)
            from_version = payload["plugin"]["from_version"]
            failure_kind = (
                payload.get("failure", {}).get("kind")
                if isinstance(payload.get("failure"), dict)
                else None
            )
            failed_before_verified_install = state in {
                "refreshing",
                "refresh_failed",
                "installing",
                "install_failed",
            } or (
                state == "recovery_required"
                and failure_kind == "marketplace_refresh_verification_failed"
            )
            if (
                failed_before_verified_install
                and plugin["version"] == from_version
                and not errors
            ):
                hook = hook_snapshot(
                    root,
                    payload["plugin"]["name"],
                    payload["plugin"]["marketplace"],
                    from_version,
                )
                if hook != payload["snapshot"]["hook"]:
                    raise TransactionError("old Plugin Hook files changed after failed install")
                runtime_hook = runtime_hook_snapshot(project_root, selector)
                if runtime_hook != payload["snapshot"]["runtime_hook"]:
                    raise TransactionError("old runtime Hook state changed after failed install")
                mcp = mcp_runtime_snapshot(
                    root,
                    payload["plugin"]["name"],
                    payload["plugin"]["marketplace"],
                    from_version,
                    allow_matching_deleted_backup=True,
                )
                if mcp != payload["snapshot"]["mcp"]:
                    raise TransactionError("old Plugin MCP runtime changed after failed install")
                payload["state"] = "failed_safe"
                payload["completed_at"] = timestamp()
                payload["recovery_session_digest"] = current_session
                payload["recovered"] = {
                    "plugin": plugin,
                    "marketplace": current_marketplace,
                    "hook": hook,
                    "runtime_hook": runtime_hook,
                    "mcp": mcp,
                }
                atomic_json_write(path, payload)
                return {
                    "transaction_id": transaction_id,
                    "state": "failed_safe",
                    "plugin": selector,
                    "installed_version": plugin["version"],
                    "target_version": target,
                    "target_installed": False,
                    "action_required": "fix_install_cause_then_prepare_a_new_transaction",
                }
            if plugin["version"] != target:
                errors.append(
                    f"installed plugin version {plugin['version']} does not match target {target}"
                )
            else:
                expected_marketplace = payload.get("marketplace_after_refresh")
                if not isinstance(expected_marketplace, dict):
                    errors.append("post-refresh marketplace snapshot is missing")
                elif current_marketplace is not None and not marketplace_snapshot_matches(
                    expected_marketplace, current_marketplace
                ):
                    errors.append("marketplace snapshot changed after refresh")
                hook = hook_snapshot(
                    root,
                    payload["plugin"]["name"],
                    payload["plugin"]["marketplace"],
                    target,
                )
                runtime_hook = runtime_hook_snapshot(project_root, selector)
                mcp = mcp_runtime_snapshot(
                    root,
                    payload["plugin"]["name"],
                    payload["plugin"]["marketplace"],
                    target,
                    allow_matching_deleted_backup=True,
                )
        except TransactionError as exc:
            errors.append(str(exc))
        if errors:
            payload["state"] = "recovery_required"
            payload["last_recovery_at"] = timestamp()
            payload["failure"] = {"kind": "recovery_checks_failed", "messages": errors}
            atomic_json_write(path, payload)
            raise TransactionError("recovery checks failed: " + "; ".join(errors))
        payload["state"] = "completed"
        payload["completed_at"] = timestamp()
        payload["recovery_session_digest"] = current_session
        payload["recovered"] = {
            "plugin": plugin,
            "marketplace": current_marketplace,
            "hook": hook,
            "runtime_hook": runtime_hook,
            "mcp": mcp,
        }
        payload.pop("failure", None)
        atomic_json_write(path, payload)
    return {
        "transaction_id": transaction_id,
        "state": "completed",
        "plugin": selector,
        "installed_version": plugin["version"],
        "project_root": str(project_root),
        "task": payload["snapshot"]["task"],
    }


HISTORICAL_DRIFT_ERRORS = {
    "project Git snapshot changed",
    "CODEX_HOME Git snapshot changed",
    "current Trellis task changed",
}


def finalize_recovery(args: argparse.Namespace) -> dict[str, Any]:
    """Safely close a restarted, target-installed transaction with stale history.

    This is deliberately narrower than recover(): it never repairs the historical
    snapshot, and it only ends a transaction once the current installation has
    independently passed all safety checks. The original failure remains intact
    for auditability.
    """
    root = code_home()
    state_root = transaction_root(root)
    transaction_id = resolve_transaction_id(state_root, args.transaction)
    with transaction_lock(state_root):
        path, payload = load_transaction(state_root, transaction_id)
        if payload.get("state") != "recovery_required":
            raise TransactionError(
                "only a recovery_required transaction can be finalized for historical drift"
            )
        current_session = session_digest()
        current_process = codex_process_identity()
        if not restart_proven(payload, current_session, current_process):
            raise TransactionError(
                "finalize-recovery requires a newly started Codex process; "
                "CODEX_THREAD_ID may remain stable when the same conversation is resumed"
            )
        project_root = require_project_root(args.project_root)
        if project_root != require_project_root(str(payload.get("project_root", ""))):
            raise TransactionError("provided project root does not match the transaction")
        other_active = [
            candidate
            for candidate in unexpired_active_transactions(state_root)
            if candidate != transaction_id
        ]
        if other_active:
            raise TransactionError(
                "another plugin update transaction is active: " + other_active[0]
            )

        historical_drift = compare_snapshot(root, project_root, payload.get("snapshot", {}))
        unexpected = [
            error for error in historical_drift if error not in HISTORICAL_DRIFT_ERRORS
        ]
        if unexpected:
            raise TransactionError(
                "historical-drift finalization checks failed: " + "; ".join(unexpected)
            )
        if not historical_drift:
            raise TransactionError(
                "no historical snapshot drift was found; use recover instead of finalize-recovery"
            )

        selector = payload["plugin"]["selector"]
        target = payload["plugin"]["target_version"]
        try:
            plugin = installed_plugin(selector)
            if plugin["version"] != target:
                raise TransactionError(
                    f"installed plugin version {plugin['version']} does not match target {target}"
                )
            current_marketplace = marketplace_snapshot(payload["plugin"]["marketplace"])
            expected_marketplace = payload.get("marketplace_after_refresh")
            if not isinstance(expected_marketplace, dict):
                raise TransactionError("post-refresh marketplace snapshot is missing")
            if not marketplace_snapshot_matches(expected_marketplace, current_marketplace):
                raise TransactionError("marketplace snapshot changed after refresh")
            hook = hook_snapshot(
                root,
                payload["plugin"]["name"],
                payload["plugin"]["marketplace"],
                target,
            )
            runtime_hook = runtime_hook_snapshot(project_root, selector)
            mcp = mcp_runtime_snapshot(
                root,
                payload["plugin"]["name"],
                payload["plugin"]["marketplace"],
                target,
                allow_matching_deleted_backup=True,
            )
        except TransactionError as exc:
            raise TransactionError(
                "current installation cannot be finalized safely: " + str(exc)
            ) from exc

        payload["state"] = "failed_safe"
        payload["completed_at"] = timestamp()
        payload["finalization"] = {
            "kind": "historical_snapshot_drift",
            "operator_confirmation": "explicit_cli_flag",
            "finalized_at": payload["completed_at"],
            "session_digest": current_session,
            "process": current_process,
            "historical_drift": sorted(historical_drift),
            "target_installed": True,
            "current": {
                "plugin": plugin,
                "marketplace": current_marketplace,
                "hook": hook,
                "runtime_hook": runtime_hook,
                "mcp": mcp,
            },
            "remaining_risk": "historical prepare snapshot is intentionally not replayed",
        }
        atomic_json_write(path, payload)
    return {
        "transaction_id": transaction_id,
        "state": "failed_safe",
        "plugin": selector,
        "installed_version": plugin["version"],
        "target_installed": True,
        "historical_drift": sorted(historical_drift),
        "action_required": "prepare_a_new_transaction_for_future_updates",
    }


def status(args: argparse.Namespace) -> dict[str, Any]:
    root = code_home()
    state_root = transaction_root(root)
    transaction_id = resolve_transaction_id(state_root, args.transaction)
    _, payload = load_transaction(state_root, transaction_id)
    effective_state = payload.get("state")
    if effective_state == "prepared":
        try:
            if parse_timestamp(payload.get("expires_at")) <= utc_now():
                effective_state = "expired"
        except TransactionError:
            effective_state = "invalid"
    return {
        "transaction_id": transaction_id,
        "state": payload.get("state"),
        "effective_state": effective_state,
        "plugin": payload.get("plugin"),
        "project_root": payload.get("project_root"),
        "created_at": payload.get("created_at"),
        "expires_at": payload.get("expires_at"),
        "failure": payload.get("failure"),
    }


def abort(args: argparse.Namespace) -> dict[str, Any]:
    root = code_home()
    state_root = transaction_root(root)
    transaction_id = resolve_transaction_id(state_root, args.transaction)
    with transaction_lock(state_root):
        path, payload = load_transaction(state_root, transaction_id)
        if payload.get("state") != "prepared":
            raise TransactionError("only a prepared transaction can be aborted")
        if payload.get("origin_session_digest") != session_digest():
            raise TransactionError("abort must run in the session that prepared the transaction")
        plugin = installed_plugin(payload["plugin"]["selector"])
        if plugin["version"] != payload["plugin"]["from_version"]:
            raise TransactionError("plugin version changed; recover instead of aborting")
        payload["state"] = "aborted"
        payload["aborted_at"] = timestamp()
        atomic_json_write(path, payload)
    return {"transaction_id": transaction_id, "state": "aborted"}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--plugin", required=True)
    prepare_parser.add_argument("--target-version", required=True)
    prepare_parser.add_argument("--project-root", required=True)
    prepare_parser.add_argument(
        "--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES, choices=range(10, 1441)
    )
    prepare_parser.set_defaults(handler=prepare)

    install_parser = commands.add_parser("install")
    install_parser.add_argument("--transaction", required=True)
    install_parser.add_argument(
        "--timeout-seconds", type=int, default=180, choices=range(30, 1801)
    )
    install_parser.set_defaults(handler=install)

    recover_parser = commands.add_parser("recover")
    recover_parser.add_argument("--transaction", required=True)
    recover_parser.add_argument("--project-root")
    recover_parser.set_defaults(handler=recover)

    finalize_parser = commands.add_parser("finalize-recovery")
    finalize_parser.add_argument("--transaction", required=True)
    finalize_parser.add_argument("--project-root", required=True)
    finalize_parser.add_argument(
        "--confirm-historical-drift",
        action="store_true",
        required=True,
        help="explicitly acknowledge that only the historical snapshot is being closed",
    )
    finalize_parser.set_defaults(handler=finalize_recovery)

    status_parser = commands.add_parser("status")
    status_parser.add_argument("--transaction", required=True)
    status_parser.set_defaults(handler=status)

    abort_parser = commands.add_parser("abort")
    abort_parser.add_argument("--transaction", required=True)
    abort_parser.set_defaults(handler=abort)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.handler(args)
    except TransactionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
