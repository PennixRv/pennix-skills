"""Manage the official Cognee Codex plugin through Codex's native owner."""

from __future__ import annotations

from pathlib import Path

from . import codex_plugins, codex_static


VERSION = "1.7.4"
PLUGIN = "cognee@cognee"
MARKETPLACE = "cognee"
SOURCE = "https://github.com/topoteretes/cognee-integrations"
REF = "201ba4c8e824060b40b65ea5129a1d8c964ae798"
SPARSE = ["integrations/codex/plugins/cognee"]


def _plugin(codex_home: Path) -> dict | None:
    try:
        return codex_plugins.installed_plugin(codex_home, PLUGIN)
    except codex_plugins.PluginError as error:
        raise codex_static.StaticError("Cognee native plugin state is unavailable") from error


def state(codex_home: Path, config: Path | None = None, api_url: str | None = None) -> str:
    del config, api_url
    plugin = _plugin(codex_home)
    if plugin is None:
        return "not-configured"
    if plugin.get("version") != VERSION or plugin.get("enabled") is not True:
        return "drifted"
    source = plugin.get("source")
    if not isinstance(source, dict) or source.get("source") != "git" or source.get("ref") != REF:
        return "drifted"
    return "configured"


def install(codex_home: Path) -> None:
    codex_plugins.install_plugin(
        codex_home,
        {
            "id": PLUGIN,
            "marketplace": {
                "name": MARKETPLACE,
                "source": SOURCE,
                "ref": REF,
                "sparse": SPARSE,
            },
        },
    )
    if state(codex_home) != "configured":
        raise codex_plugins.PluginError("Cognee native plugin verification failed")


def configure(codex_home: Path, config: Path | None = None, api_url: str | None = None) -> None:
    del config, api_url
    if state(codex_home) != "configured":
        raise codex_plugins.PluginError("Cognee native plugin is not installed at the pinned source")


def remove(codex_home: Path, config: Path | None = None, api_url: str | None = None) -> None:
    del config, api_url
    if _plugin(codex_home) is None:
        return
    codex_plugins.remove_plugin(codex_home, PLUGIN)
