"""Use Codex's native plugin lifecycle without parsing its config file."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class PluginError(RuntimeError):
    """Raised when Codex cannot safely manage a plugin."""


def run_json(codex_home: Path, *arguments: str) -> dict[str, Any]:
    codex = shutil.which("codex")
    if not codex:
        raise PluginError("Codex CLI is unavailable")
    try:
        result = subprocess.run(
            [codex, "plugin", *arguments],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            env={**os.environ, "CODEX_HOME": str(codex_home)},
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PluginError(f"Codex plugin command failed to start: {error}") from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        raise PluginError(f"Codex plugin command failed: {detail}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise PluginError("Codex plugin command returned invalid JSON") from error
    if not isinstance(value, dict):
        raise PluginError("Codex plugin command returned an invalid JSON object")
    return value


def installed_plugin(codex_home: Path, plugin_id: str) -> dict[str, Any] | None:
    installed = run_json(codex_home, "list", "--json").get("installed")
    if not isinstance(installed, list):
        raise PluginError("Codex plugin list has no installed array")
    for plugin in installed:
        if isinstance(plugin, dict) and plugin.get("pluginId") == plugin_id:
            return plugin
    return None


def marketplace_status(codex_home: Path, name: str, source: str) -> str:
    marketplaces = run_json(codex_home, "marketplace", "list", "--json").get("marketplaces")
    if not isinstance(marketplaces, list):
        raise PluginError("Codex marketplace list has no marketplaces array")
    for marketplace in marketplaces:
        if not isinstance(marketplace, dict) or marketplace.get("name") != name:
            continue
        current = marketplace.get("marketplaceSource")
        if isinstance(current, dict) and current.get("source") == source:
            return "matching-source"
        return "different-source"
    return "absent"


def install_plugin(codex_home: Path, plugin: dict[str, Any]) -> None:
    marketplace = plugin["marketplace"]
    state = marketplace_status(codex_home, marketplace["name"], marketplace["source"])
    if state != "absent":
        raise PluginError(f"marketplace is already present and cannot be ref-verified: {state}")
    add_marketplace = ["marketplace", "add", marketplace["source"], "--ref", marketplace["ref"], "--json"]
    for sparse_path in marketplace.get("sparse", []):
        add_marketplace.extend(["--sparse", sparse_path])
    try:
        run_json(codex_home, *add_marketplace)
        run_json(codex_home, "add", plugin["id"], "--json")
    except PluginError as error:
        try:
            installed = installed_plugin(codex_home, plugin["id"])
            state = marketplace_status(codex_home, marketplace["name"], marketplace["source"])
            if installed is None and state == "matching-source":
                run_json(codex_home, "marketplace", "remove", marketplace["name"], "--json")
            elif installed is None:
                raise PluginError(f"marketplace recovery is unsafe: {state}")
        except PluginError as rollback_error:
            raise PluginError(f"plugin install failed and marketplace rollback failed: {rollback_error}") from error
        raise


def remove_plugin(codex_home: Path, plugin_id: str) -> None:
    run_json(codex_home, "remove", plugin_id, "--json")
