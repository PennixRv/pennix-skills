"""Manage the official Cognee Codex plugin through Codex's native owner."""

from __future__ import annotations

import json
import io
import re
import subprocess
import tarfile
import tomllib
from pathlib import Path

from . import codex_plugins, codex_static


POLICY_BEGIN = "# pennix-cognee-plugin-policy:begin"
POLICY_END = "# pennix-cognee-plugin-policy:end"


def _contract() -> tuple[str, dict]:
    catalog_path = Path(__file__).resolve().parents[2] / "references" / "component-versions.json"
    try:
        component = json.loads(catalog_path.read_text(encoding="utf-8"))["components"]["cognee-coding-agents"]
        return component["approved_version"], component["plugin"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise codex_static.StaticError("Cognee plugin catalog contract is unavailable") from error


def _policy_state(codex_home: Path) -> str:
    contents = codex_static.read(codex_home / "config.toml")
    if contents.count(POLICY_BEGIN) != contents.count(POLICY_END) or contents.count(POLICY_BEGIN) > 1:
        return "drifted"
    owned = contents.count(POLICY_BEGIN) == 1
    if owned:
        start = contents.index(POLICY_BEGIN)
        if contents.index(POLICY_END) < start:
            return "drifted"
        finish = contents.index(POLICY_END, start) + len(POLICY_END)
        expected = f'{POLICY_BEGIN}\n[plugins."cognee@cognee"]\nenabled = false\n{POLICY_END}'
        if contents[start:finish] != expected:
            return "drifted"
    try:
        plugin = tomllib.loads(contents).get("plugins", {}).get("cognee@cognee")
    except (tomllib.TOMLDecodeError, AttributeError):
        return "drifted"
    if isinstance(plugin, dict) and plugin.get("enabled") is False:
        return "configured"
    return "drifted" if plugin is not None else "missing"


def _restore_native_install_policy(codex_home: Path) -> None:
    # Called only after native plugin add changed a previously disabled setting.
    path = codex_home / "config.toml"
    contents = codex_static.read(path)
    pattern = r'(?m)(^\[plugins\."cognee@cognee"\]\n(?:(?!\[).+\n)*?enabled = )true(?=\n)'
    restored, count = re.subn(pattern, r'\g<1>false', contents)
    if count != 1:
        raise codex_static.StaticError("Native Cognee installation changed the policy unexpectedly")
    codex_static.write(path, restored)



def _ensure_global_disabled(codex_home: Path) -> None:
    state = _policy_state(codex_home)
    if state == "configured":
        return
    if state != "missing":
        raise codex_static.StaticError("Cognee global plugin policy conflicts with Codex configuration")
    path = codex_home / "config.toml"
    contents = codex_static.read(path)
    block = f'{POLICY_BEGIN}\n[plugins."cognee@cognee"]\nenabled = false\n{POLICY_END}\n'
    separator = "\n" if contents and not contents.endswith("\n\n") else ""
    codex_static.write(path, contents + separator + block)
    if _policy_state(codex_home) != "configured":
        raise codex_static.StaticError("Cognee global plugin policy write failed")


def _remove_global_policy(codex_home: Path) -> None:
    if POLICY_BEGIN not in codex_static.read(codex_home / "config.toml"):
        return
    if _policy_state(codex_home) != "configured":
        raise codex_static.StaticError("Cognee global plugin policy is drifted")
    path = codex_home / "config.toml"
    contents = codex_static.read(path)
    start = contents.index(POLICY_BEGIN)
    finish = contents.index(POLICY_END, start) + len(POLICY_END)
    if contents[finish : finish + 2] == "\n\n":
        finish += 2
    elif contents[finish : finish + 1] == "\n":
        finish += 1
    codex_static.write(path, contents[:start] + contents[finish:])


def _plugin(codex_home: Path, plugin_id: str) -> dict | None:
    try:
        return codex_plugins.installed_plugin(codex_home, plugin_id)
    except codex_plugins.PluginError as error:
        raise codex_static.StaticError("Cognee native plugin state is unavailable") from error


def _content_matches(codex_home: Path, version: str, contract: dict) -> bool:
    marketplaces = codex_plugins.run_json(codex_home, "marketplace", "list", "--json")["marketplaces"]
    matches = [item for item in marketplaces if item.get("name") == contract["marketplace"]["name"]]
    if len(matches) != 1:
        return False
    source_path = "integrations/codex/plugins/cognee"
    installed = codex_home / "plugins" / "cache" / "cognee" / "cognee" / version
    try:
        archive = subprocess.run(
            ["git", "-C", matches[0]["root"], "archive", contract["marketplace"]["ref"], source_path],
            capture_output=True, timeout=15, check=True,
        ).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
            files = [item for item in tree if item.isfile()]
            return bool(files) and all(
                not (installed / item.name.removeprefix(source_path + "/")).is_symlink()
                and (installed / item.name.removeprefix(source_path + "/")).read_bytes() == tree.extractfile(item).read()
                for item in files
            )
    except (OSError, KeyError, subprocess.SubprocessError, tarfile.TarError):
        return False


def inspect(codex_home: Path) -> tuple[str, str | None]:
    version, contract = _contract()
    plugin = _plugin(codex_home, contract["id"])
    if plugin is None:
        return "not-configured", None
    observed = plugin.get("version")
    if observed != version or plugin.get("enabled") is not False:
        return "drifted", observed
    marketplace = contract["marketplace"]
    try:
        marketplace_state = codex_plugins.marketplace_status(
            codex_home, marketplace["name"], marketplace["source"], marketplace["ref"]
        )
    except (KeyError, codex_plugins.PluginError):
        return "drifted", observed
    if marketplace_state != "matching-ref" or _policy_state(codex_home) != "configured":
        return "drifted", observed
    if not _content_matches(codex_home, version, contract):
        return "drifted", observed
    return "configured", observed


def state(codex_home: Path) -> str:
    return inspect(codex_home)[0]


def install(codex_home: Path) -> None:
    _ensure_global_disabled(codex_home)
    version, contract = _contract()
    plugin_id = contract["id"]
    installed = _plugin(codex_home, plugin_id)
    if installed is None:
        codex_plugins.install_plugin(codex_home, contract)
        if _policy_state(codex_home) != "configured":
            _restore_native_install_policy(codex_home)
    elif installed.get("version") != version or installed.get("enabled") is not False:
        raise codex_plugins.PluginError("an unmanaged Cognee plugin installation blocks the pinned install")
    if state(codex_home) != "configured":
        raise codex_plugins.PluginError("Cognee native plugin verification failed")


def launcher_path() -> Path:
    return Path.home() / ".local" / "bin" / "pennix-codex"


def launcher_target(codex_home: Path) -> Path:
    return codex_home / "skills" / "pennix-skills" / "pennix-cognee-memory" / "scripts" / "codex.py"


def launcher_state(codex_home: Path) -> str:
    path = launcher_path()
    if path.is_symlink():
        return "configured" if path.readlink() == launcher_target(codex_home) else "drifted"
    return "drifted" if path.exists() else "not-configured"


def _ensure_launcher(codex_home: Path) -> None:
    state = launcher_state(codex_home)
    if state == "configured":
        return
    if state != "not-configured":
        raise codex_static.StaticError("Pennix Codex launcher conflicts with an existing entry")
    target = launcher_target(codex_home)
    if not target.is_file() or not target.stat().st_mode & 0o111:
        raise codex_static.StaticError("Installed Pennix Cognee launcher is unavailable")
    path = launcher_path()
    if any(parent.is_symlink() for parent in path.absolute().parents):
        raise codex_static.StaticError("Pennix Codex launcher parent is linked")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


def configure(codex_home: Path, config: Path | None = None, api_url: str | None = None) -> None:
    del config, api_url
    _ensure_global_disabled(codex_home)
    if state(codex_home) != "configured":
        raise codex_plugins.PluginError("Cognee native plugin is not installed at the pinned source")
    _ensure_launcher(codex_home)


def remove(codex_home: Path, config: Path | None = None, api_url: str | None = None) -> None:
    del config, api_url
    _, contract = _contract()
    plugin_id = contract["id"]
    _remove_global_policy(codex_home)
    if _plugin(codex_home, plugin_id) is not None:
        codex_plugins.remove_plugin(codex_home, plugin_id)
    if launcher_state(codex_home) == "configured":
        launcher_path().unlink()
