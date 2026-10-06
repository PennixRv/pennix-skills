"""Configure the optional native SiYuan MCP connection without data transport."""

from __future__ import annotations

import importlib.util
import json
import shlex
import sys
import tomllib
from pathlib import Path

from . import codex_static, configuration


BEGIN = "# pennix-siyuan:begin"
END = "# pennix-siyuan:end"


def helper_path(codex_home: Path) -> Path:
    return codex_home / "skills/pennix-skills/pennix-siyuan-memory/scripts/mcp_headers.py"


def _helper():
    path = Path(__file__).resolve().parents[3] / "pennix-siyuan-memory/scripts/mcp_headers.py"
    spec = importlib.util.spec_from_file_location("pennix_siyuan_headers", path)
    if spec is None or spec.loader is None:
        raise configuration.ConfigurationError("SiYuan helper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _entry(codex_home: Path, value: dict) -> dict:
    return {"url": value["url"], "http_headers_helper": shlex.join([sys.executable, str(helper_path(codex_home))]), "required": False}


def _section(codex_home: Path, value: dict) -> str:
    entry = _entry(codex_home, value)
    return f'{BEGIN}\n[mcp_servers.siyuan]\nurl = {json.dumps(entry["url"])}\nhttp_headers_helper = {json.dumps(entry["http_headers_helper"])}\nrequired = false\n{END}\n'


def merged_config(contents: str, codex_home: Path, value: dict, previous: dict | None = None) -> str:
    """Refuse unowned or edited entries and preserve every unrelated byte."""
    try:
        observed = tomllib.loads(contents).get("mcp_servers", {}).get("siyuan")
    except (tomllib.TOMLDecodeError, AttributeError):
        raise configuration.ConfigurationError("Codex config invalid") from None
    if BEGIN in contents or END in contents:
        if contents.count(BEGIN) != 1 or contents.count(END) != 1 or previous is None or contents.index(END) < contents.index(BEGIN):
            raise configuration.ConfigurationError("SiYuan config ownership is unclear")
        start = contents.index(BEGIN)
        finish = contents.index(END, start) + len(END)
        if contents[start:finish] != _section(codex_home, previous).rstrip("\n") or observed != _entry(codex_home, previous):
            raise configuration.ConfigurationError("SiYuan config drifted")
        return contents[:start] + _section(codex_home, value).rstrip("\n") + contents[finish:]
    if observed is not None:
        raise configuration.ConfigurationError("SiYuan config is user-owned")
    return contents + ("\n" if contents and not contents.endswith("\n") else "") + "\n" + _section(codex_home, value)


def target_state(codex_home: Path) -> str:
    helper = _helper()
    if not helper.connection_path().exists() and not helper.connection_path().is_symlink():
        return "not-configured"
    try:
        value = helper.read_connection()
        contents = codex_static.read(codex_home / "config.toml")
        merged_config(contents, codex_home, value, value)
        if BEGIN not in contents or not helper_path(codex_home).is_file():
            return "not-configured"
    except (helper.ConnectionError, configuration.ConfigurationError, codex_static.StaticError):
        return "blocked"
    return "configured"


def configure(codex_home: Path) -> str:
    helper = _helper()
    path = helper.connection_path()
    previous = None
    try:
        if path.exists() or path.is_symlink():
            previous = helper.read_connection()
        contents = codex_static.read(codex_home / "config.toml")
        # Check ownership before collecting or storing any operator secret.
        probe = previous or {"url": "https://example.invalid/mcp"}
        merged_config(contents, codex_home, probe, previous)
        if not helper_path(codex_home).is_file():
            raise configuration.ConfigurationError("installed SiYuan helper unavailable")
        value = helper.validate({
            "schema": 1,
            "url": configuration._read_tty("SiYuan HTTPS MCP URL: "),
            "default_notebook": configuration._read_tty("Default notebook ID: "),
            "api_token": configuration._read_tty("SiYuan API Token (目标内核：设置 → 鉴权 → API token；不是登录密码): ", secret=True),
        })
        updated = merged_config(contents, codex_home, value, previous)
        # Recheck concurrent config changes before a write.
        if codex_static.read(codex_home / "config.toml") != contents:
            raise configuration.ConfigurationError("Codex config changed concurrently")
        configuration._write_private_json(path, value)
        try:
            codex_static.write(codex_home / "config.toml", updated)
        except (OSError, codex_static.StaticError):
            # Restore only a proven unwritten config and our exact private write.
            if codex_static.read(codex_home / "config.toml") == contents and helper.read_connection() == value:
                if previous is None:
                    path.unlink()
                else:
                    configuration._write_private_json(path, previous)
            raise configuration.ConfigurationError("SiYuan config write failed; verify local state") from None
    except helper.ConnectionError:
        raise configuration.ConfigurationError("SiYuan connection invalid or unsafe") from None
    return target_state(codex_home)
