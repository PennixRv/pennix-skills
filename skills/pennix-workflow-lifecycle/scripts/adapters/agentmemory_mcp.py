"""Configure the pinned official stdio client without copying its secret."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

from . import codex_static


VERSION = "0.9.29"
PLUGIN = "agentmemory@agentmemory"
PLUGIN_TABLE = '[plugins."agentmemory@agentmemory".mcp_servers.agentmemory]'


def directory() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    if not base.is_absolute():
        raise codex_static.StaticError("AgentMemory data directory must be absolute")
    target = base / "pennix-workflow-lifecycle/agentmemory-mcp"
    codex_static.assert_no_symlink_ancestor(target)
    return target


def expected(config: Path, api_url: str) -> dict:
    node = shutil.which("node")
    if not node:
        raise codex_static.StaticError("Node with --env-file support is required")
    return {"command": node, "args": ["--env-file=" + str(config), str(directory() / "node_modules/@agentmemory/mcp/bin.mjs")], "env": {"AGENTMEMORY_FORCE_PROXY": "true", "AGENTMEMORY_URL": api_url.rstrip("/")}}


def _config(codex_home: Path) -> tuple[str, dict]:
    contents = codex_static.read(codex_home / "config.toml")
    try:
        return contents, tomllib.loads(contents)
    except tomllib.TOMLDecodeError as error:
        raise codex_static.StaticError("Codex config is invalid") from error


def _pinned() -> bool:
    for name in ("@agentmemory/mcp", "@agentmemory/agentmemory"):
        try:
            package = json.loads((directory() / "node_modules" / name / "package.json").read_text())
        except (OSError, ValueError):
            return False
        if package.get("version") != VERSION:
            return False
    return True


def state(codex_home: Path, config: Path, api_url: str) -> str:
    _, value = _config(codex_home)
    server = value.get("mcp_servers", {}).get("agentmemory")
    disabled = value.get("plugins", {}).get(PLUGIN, {}).get("mcp_servers", {}).get("agentmemory", {}).get("enabled") is False
    return "configured" if _pinned() and server == expected(config, api_url) and disabled else "drifted"


def _run(arguments: list[str], codex_home: Path) -> None:
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=120, check=False, env={**os.environ, "CODEX_HOME": str(codex_home)})
    except (OSError, subprocess.TimeoutExpired) as error:
        raise codex_static.StaticError("AgentMemory client owner command failed") from error
    if result.returncode:
        # Do not echo owner stderr: it can contain private configuration.
        raise codex_static.StaticError("AgentMemory client owner command failed")


def _managed(server: object, wanted: dict) -> bool:
    legacy = str(directory() / "node_modules/.bin/agentmemory-mcp")
    return server is None or server == wanted or server == {"command": legacy}


def _plugin_policy(contents: str, *, remove: bool = False) -> str:
    pattern = r'(?m)^\[plugins\."agentmemory@agentmemory"\.mcp_servers\.agentmemory\]\s*\n([^\[]*)'
    match = re.search(pattern, contents)
    if not match:
        return contents if remove else contents.rstrip() + "\n\n" + PLUGIN_TABLE + "\nenabled = false\n"
    body = match.group(1)
    if tomllib.loads(PLUGIN_TABLE + "\n" + body)["plugins"][PLUGIN]["mcp_servers"]["agentmemory"] != {"enabled": False}:
        raise codex_static.StaticError("AgentMemory plugin MCP policy is not lifecycle-owned")
    return contents[:match.start()] + contents[match.end():] if remove else contents


def configure(codex_home: Path, config: Path, api_url: str) -> None:
    wanted = expected(config, api_url)
    contents, value = _config(codex_home)
    if not _managed(value.get("mcp_servers", {}).get("agentmemory"), wanted):
        raise codex_static.StaticError("AgentMemory MCP config has an unmanaged owner")
    _plugin_policy(contents)  # Validate before installing or changing config.
    codex, npm = shutil.which("codex"), shutil.which("npm")
    if not codex or not npm:
        raise codex_static.StaticError("Codex and npm are required")
    _run([wanted["command"], "--env-file=" + str(config), "--eval", ""], codex_home)
    if not _pinned():
        _run([npm, "install", "--prefix", str(directory()), "--no-save", "--package-lock=false", "--no-audit", "--no-fund", "@agentmemory/mcp@" + VERSION, "@agentmemory/agentmemory@" + VERSION], codex_home)
    _run([codex, "mcp", "add", "agentmemory", "--env", "AGENTMEMORY_FORCE_PROXY=true", "--env", "AGENTMEMORY_URL=" + api_url.rstrip("/"), "--", wanted["command"], *wanted["args"]], codex_home)
    contents, _ = _config(codex_home)
    codex_static.write(codex_home / "config.toml", _plugin_policy(contents))
    if state(codex_home, config, api_url) != "configured":
        raise codex_static.StaticError("AgentMemory MCP configuration verification failed")


def remove(codex_home: Path, config: Path, api_url: str) -> None:
    if directory().exists() and (not _pinned() or {path.name for path in directory().iterdir()} != {"node_modules"}):
        raise codex_static.StaticError("AgentMemory npm directory is not the pinned pair")
    contents, value = _config(codex_home)
    server = value.get("mcp_servers", {}).get("agentmemory")
    if not _managed(server, expected(config, api_url)):
        raise codex_static.StaticError("AgentMemory MCP config has an unmanaged owner")
    _plugin_policy(contents, remove=True)
    if server is not None:
        codex = shutil.which("codex")
        if not codex:
            raise codex_static.StaticError("Codex is required")
        _run([codex, "mcp", "remove", "agentmemory"], codex_home)
    contents, _ = _config(codex_home)
    codex_static.write(codex_home / "config.toml", _plugin_policy(contents, remove=True))
    target = directory()
    if target.exists():
        shutil.rmtree(target)
