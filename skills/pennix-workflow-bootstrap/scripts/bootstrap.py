#!/usr/bin/env python3
"""Discover and directly manage the Pennix workflow lifecycle."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from adapters import codex_plugins, codex_static, upstream
import host


SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
DEFAULT_CATALOG = SKILL_ROOT / "references" / "component-versions.json"
VERSION_RE = re.compile(r"(?<![A-Za-z0-9])v?(\d+(?:\.\d+)+(?:[A-Za-z][A-Za-z0-9.-]*)?)")
PACKAGE_NAME = re.compile(r"^[A-Za-z0-9@._+:/-]+$")
PLUGIN_ID = re.compile(r"^[a-z0-9][a-z0-9-]*@[a-z0-9][a-z0-9-]*$")
PLUGIN_REF = re.compile(r"^[A-Za-z0-9._-]+$")
class BootstrapError(RuntimeError):
    """Raised when bootstrap cannot safely continue."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def valid_npm_registry(value: str) -> bool:
    parsed = urlparse(value)
    return (
        value == value.strip()
        and parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )


def valid_plugin(value: Any) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not PLUGIN_ID.fullmatch(value["id"]):
        return False
    marketplace = value.get("marketplace")
    if not isinstance(marketplace, dict):
        return False
    name = marketplace.get("name")
    source = marketplace.get("source")
    ref = marketplace.get("ref")
    sparse = marketplace.get("sparse", [])
    parsed = urlparse(source) if isinstance(source, str) else None
    return (
        isinstance(name, str)
        and value["id"].endswith(f"@{name}")
        and isinstance(source, str)
        and parsed is not None
        and parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and isinstance(ref, str)
        and bool(PLUGIN_REF.fullmatch(ref))
        and isinstance(sparse, list)
        and all(
            isinstance(path, str)
            and bool(path)
            and not path.startswith("/")
            and ".." not in Path(path).parts
            for path in sparse
        )
    )


def load_catalog(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BootstrapError(f"cannot read catalog: {path}: {error}") from error
    components = value.get("components") if isinstance(value, dict) else None
    if not isinstance(value, dict) or value.get("schema") != 1 or not isinstance(components, dict) or not components:
        raise BootstrapError("catalog must contain schema 1 and non-empty components")
    for key, component in components.items():
        required = ("approved_version", "source", "owner", "scope", "verify_key")
        if not isinstance(component, dict) or any(name not in component for name in required):
            raise BootstrapError(f"catalog component is incomplete: {key}")
        package = component.get("package")
        if package is not None and (
            not isinstance(package, dict)
            or package.get("source") not in {"official", "aur", "npm"}
            or not isinstance(package.get("name"), str)
            or not PACKAGE_NAME.fullmatch(package["name"])
            or (package.get("source") == "npm" and not isinstance(package.get("registry"), str))
            or (package.get("source") == "npm" and not valid_npm_registry(package["registry"]))
            or (package.get("source") != "npm" and "registry" in package)
        ):
            raise BootstrapError(f"catalog package metadata is invalid: {key}")
        plugin = component.get("plugin")
        if plugin is not None and (package is not None or not valid_plugin(plugin)):
            raise BootstrapError(f"catalog plugin metadata is invalid: {key}")
        conflicts = component.get("conflicts", [])
        if not isinstance(conflicts, list) or not all(
            isinstance(name, str) and PACKAGE_NAME.fullmatch(name) for name in conflicts
        ):
            raise BootstrapError(f"catalog conflicts metadata is invalid: {key}")
        native_owner_reason = component.get("native_owner_reason")
        if native_owner_reason is not None and (
            not isinstance(native_owner_reason, str) or not native_owner_reason.strip()
        ):
            raise BootstrapError(f"catalog native owner metadata is invalid: {key}")
        try:
            upstream.validate_component(component)
        except upstream.UpstreamInspectionError as error:
            raise BootstrapError(f"catalog upstream inspection metadata is invalid: {key}: {error}") from error
    return value


def normalize_version(raw: str) -> str | None:
    match = VERSION_RE.search(raw.replace("_", ""))
    return match.group(1) if match else None


def parse_package_owner(output: str) -> str | None:
    match = re.search(r"is owned by\s+(\S+)", output)
    return match.group(1) if match else None


def installed_package_owner(command: str) -> str | None:
    pacman = shutil.which("pacman")
    if not pacman:
        return None
    try:
        result = subprocess.run(
            [pacman, "-Qo", command],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    return parse_package_owner((result.stdout or result.stderr).strip())


def installed_npm_version(package: str) -> str | None:
    npm = shutil.which("npm")
    if not npm:
        return None
    try:
        result = subprocess.run(
            [npm, "list", "--global", "--depth=0", "--json", package],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    try:
        dependencies = json.loads(result.stdout).get("dependencies", {})
        version = dependencies.get(package, {}).get("version")
    except (AttributeError, json.JSONDecodeError):
        return None
    return version if isinstance(version, str) else None


def probe_component(component: dict[str, Any], codex_home: Path | None = None) -> tuple[str, str | None]:
    plugin = component.get("plugin")
    if isinstance(plugin, dict):
        target_home = codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        try:
            installed = codex_plugins.installed_plugin(target_home, plugin["id"])
        except codex_plugins.PluginError:
            return "unknown", None
        if installed is None:
            return "missing", None
        observed = installed.get("version")
        if not isinstance(observed, str) or not isinstance(installed.get("enabled"), bool):
            return "unknown", observed if isinstance(observed, str) else None
        expected = normalize_version(str(component["approved_version"]))
        return (
            "match" if installed["enabled"] and normalize_version(observed) == expected else "drifted",
            observed,
        )
    probe = component.get("probe")
    if not probe:
        package = component.get("package")
        if isinstance(package, dict) and package.get("source") == "npm":
            observed = installed_npm_version(package["name"])
            if observed is None:
                return "missing", None
            expected = normalize_version(str(component["approved_version"]))
            return ("match" if normalize_version(observed) == expected else "drifted"), observed
        return "unknown", None
    command = shutil.which(str(probe))
    if not command:
        return "missing", None
    try:
        result = subprocess.run(
            [command, *[str(arg) for arg in component.get("version_args", [])]],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", None
    observed = normalize_version((result.stdout or result.stderr).strip())
    if result.returncode or observed is None:
        return "unknown", observed
    expected = normalize_version(str(component["approved_version"]))
    status = "match" if observed == expected else "drifted"
    package = component.get("package")
    if (
        status == "match"
        and isinstance(package, dict)
        and package.get("source") != "npm"
        and installed_package_owner(command) != package["name"]
    ):
        status = "drifted"
    return status, observed


def discover(args: argparse.Namespace, catalog: dict[str, Any]) -> dict[str, Any]:
    components = {}
    for key, component in catalog["components"].items():
        status, observed = probe_component(component, args.codex_home)
        package = component.get("package")
        command = shutil.which(str(component["probe"])) if component.get("probe") else None
        observed_package = (
            installed_package_owner(command)
            if isinstance(package, dict) and package.get("source") != "npm" and command
            else (
                package["name"]
                if isinstance(package, dict) and package.get("source") == "npm" and status != "missing"
                else None
            )
        )
        components[key] = {
            "status": status,
            "observed_version": observed,
            "owner": component["owner"],
            "scope": component["scope"],
            "verify_key": component["verify_key"],
            "observed_package": observed_package,
        }
    source = args.source
    source_ready = (source / "skills" / "pennix-workflow-bootstrap" / "SKILL.md").is_file()
    agents = args.codex_home / "AGENTS.md"
    config = args.codex_home / "config.toml"
    agents_state = codex_static.template_state(agents)
    config_state = codex_static.config_state(codex_static.read(config))
    return {
        "schema": 1,
        "observed_at": now(),
        "catalog": str(args.catalog),
        "source": {"path": str(source), "ready": source_ready},
        "host": host.detect_host(),
        "static": {
            "agents_path": str(agents),
            "agents_template": agents_state,
            "config_path": str(config),
            "config_install": config_state,
        },
        "components": components,
    }


def package_candidate_version(installer: str, package: str, registry: str | None = None) -> str | None:
    try:
        result = subprocess.run(
            host.package_info_command(installer, package, registry),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    if result.returncode:
        return None
    return normalize_version(result.stdout)


STATIC_COMPONENTS = {"codex-config", "codex-agents", "pennix-skills"}


def inspect_for_operation(component: dict[str, Any]) -> None:
    if not isinstance(component.get("upstream_inspection"), dict):
        return
    try:
        evidence = upstream.inspect_component(component)
    except upstream.UpstreamInspectionError as error:
        raise BootstrapError(str(error)) from error
    if evidence.get("status") != "match":
        raise BootstrapError(f"upstream inspection blocked the component: {evidence.get('status')}")


def static_operation(args: argparse.Namespace, component: str, operation: str) -> str:
    if component == "codex-config":
        path = args.codex_home / "config.toml"
        state = codex_static.config_state(codex_static.read(path))
        if operation == "uninstall":
            if state == "seeded":
                return "no-op"
            if state != "current":
                raise BootstrapError(f"refusing {state} bootstrap config: {path}")
            codex_static.remove_config_sections(path)
            return "changed"
        if state == "current":
            return "no-op"
        if state != "seeded":
            raise BootstrapError(f"refusing {state} bootstrap config: {path}")
        codex_static.apply_config(path)
        return "changed"

    if component == "codex-agents":
        path = args.codex_home / "AGENTS.md"
        state = codex_static.template_state(path)
        if operation == "uninstall":
            if state == "absent":
                return "no-op"
            if state != "current":
                raise BootstrapError(f"refusing {state} bootstrap template: {path}")
            path.unlink()
            return "changed"
        if state == "current":
            return "no-op"
        if state == "absent":
            if operation == "upgrade":
                raise BootstrapError("cannot upgrade an uninstalled AGENTS.md template")
            codex_static.apply_template(path)
            return "changed"
        raise BootstrapError(f"refusing {state} bootstrap template: {path}")

    from adapters import skills_install

    source = skills_install.resolve_source(str(args.source))
    skills_install.ensure_submodules(source, initialize=operation != "uninstall")
    skills = skills_install.discover_skills(source)
    destination = skills_install.resolve_destination(args.destination)
    if operation == "uninstall":
        existed = destination.exists()
        skills_install.uninstall_skills(skills, destination)
        return "changed" if existed else "no-op"
    else:
        skills_install.install_skills(skills, destination)
    return "changed"


def component_operation(
    args: argparse.Namespace, catalog: dict[str, Any], key: str, component: dict[str, Any], operation: str
) -> str:
    if operation != "uninstall":
        inspect_for_operation(component)
    current_host = host.detect_host()
    if not current_host["supported"]:
        raise BootstrapError(str(current_host["reason"]))
    status, _ = probe_component(component, args.codex_home)
    if status == "unknown":
        raise BootstrapError(f"cannot safely identify {key}; refusing {operation}")
    plugin = component.get("plugin")
    if operation == "uninstall":
        if status == "missing":
            return "no-op"
        if isinstance(plugin, dict):
            try:
                codex_plugins.remove_plugin(args.codex_home, plugin["id"])
            except codex_plugins.PluginError as error:
                raise BootstrapError(str(error)) from error
            if probe_component(component, args.codex_home)[0] != "missing":
                raise BootstrapError("plugin uninstall postcondition failed")
            return "changed"
        metadata = component.get("package")
        if not isinstance(metadata, dict):
            raise BootstrapError(component.get("native_owner_reason", f"{key} has no uninstall owner"))
        installer = current_host["installers"].get(metadata.get("source"))
        package_name = metadata.get("name")
        if not isinstance(installer, str) or not isinstance(package_name, str):
            raise BootstrapError(f"{key} has no supported package uninstall")
        command = shutil.which(str(component["probe"])) if component.get("probe") else None
        if metadata.get("source") != "npm" and command and installed_package_owner(command) != package_name:
            raise BootstrapError(f"{key} is not owned by {package_name}")
        try:
            result = subprocess.run(host.package_remove_command(installer, package_name), check=False)
        except (OSError, ValueError) as error:
            raise BootstrapError(f"package manager could not start: {error}") from error
        if result.returncode:
            raise BootstrapError(f"package manager failed ({result.returncode})")
        if probe_component(component, args.codex_home)[0] != "missing":
            raise BootstrapError("package uninstall postcondition failed")
        return "changed"

    if status == "match":
        return "no-op"
    if isinstance(plugin, dict):
        if operation == "upgrade":
            raise BootstrapError(f"{key} plugin upgrade belongs to the native Codex plugin owner")
        codex = catalog["components"].get("codex-cli")
        if not isinstance(codex, dict) or probe_component(codex, args.codex_home)[0] != "match":
            raise BootstrapError("Codex CLI does not match catalog")
        marketplace = plugin["marketplace"]
        try:
            if codex_plugins.marketplace_status(args.codex_home, marketplace["name"], marketplace["source"]) != "absent":
                raise BootstrapError("existing marketplace cannot be ref-verified")
            codex_plugins.install_plugin(args.codex_home, plugin)
        except codex_plugins.PluginError as error:
            raise BootstrapError(str(error)) from error
    else:
        metadata = component.get("package")
        if not isinstance(metadata, dict):
            raise BootstrapError(component.get("native_owner_reason", f"{key} requires its native owner"))
        installer = current_host["installers"].get(metadata.get("source"))
        package_name = metadata.get("name")
        registry = metadata.get("registry")
        if not isinstance(installer, str) or not isinstance(package_name, str):
            raise BootstrapError(f"{key} has no supported package installer")
        command = shutil.which(str(component["probe"])) if component.get("probe") else None
        if command and installed_package_owner(command) in component.get("conflicts", []):
            raise BootstrapError("installed command is owned by a conflicting package")
        expected = normalize_version(str(component["approved_version"]))
        if (
            metadata.get("source") == "npm"
            and status != "match"
            and normalize_version(installed_npm_version(package_name) or "") == expected
        ):
            raise BootstrapError("installed npm package does not provide an effective matching command")
        if package_candidate_version(installer, package_name, registry) != expected:
            raise BootstrapError("repository candidate does not match catalog")
        install_name = f"{package_name}@{expected}" if metadata.get("source") == "npm" else package_name
        try:
            result = subprocess.run(host.package_install_command(installer, install_name, registry), check=False)
        except (OSError, ValueError) as error:
            raise BootstrapError(f"package manager could not start: {error}") from error
        if result.returncode:
            raise BootstrapError(f"package manager failed ({result.returncode})")
    if probe_component(component, args.codex_home)[0] != "match":
        raise BootstrapError(f"{operation} postcondition failed: {key} does not match catalog")
    return "changed"


def run_lifecycle(args: argparse.Namespace, catalog: dict[str, Any]) -> None:
    if not args.component:
        raise BootstrapError(f"{args.command} requires --component")
    if not args.yes:
        raise BootstrapError(f"{args.command} requires --yes")
    current_host = host.detect_host()
    if not current_host["supported"]:
        raise BootstrapError(str(current_host["reason"]))
    component = args.component
    if component not in STATIC_COMPONENTS and component not in catalog["components"]:
        raise BootstrapError(f"unknown bootstrap component: {component}")
    if component in STATIC_COMPONENTS:
        status = static_operation(args, component, args.command)
    else:
        status = component_operation(args, catalog, component, catalog["components"][component], args.command)
    print(json.dumps({"operation": args.command, "component": component, "status": status}, ensure_ascii=False))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", "install", "upgrade", "uninstall", "verify"))
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--source", type=Path, default=SCRIPT_ROOT.parents[2])
    parser.add_argument("--destination")
    parser.add_argument("--component")
    parser.add_argument("--yes", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        args.catalog = args.catalog.expanduser().resolve()
        # Preserve symlink information so codex_static can reject unsafe targets.
        args.codex_home = args.codex_home.expanduser().absolute()
        args.source = args.source.expanduser().resolve()
        catalog = load_catalog(args.catalog)
        inventory = discover(args, catalog)
        if args.command in {"discover", "verify"}:
            print(json.dumps(inventory, ensure_ascii=False, indent=2))
        else:
            run_lifecycle(args, catalog)
        return 0
    except (BootstrapError, codex_static.StaticError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
