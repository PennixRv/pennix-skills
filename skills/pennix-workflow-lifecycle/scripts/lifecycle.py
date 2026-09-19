#!/usr/bin/env python3
"""Discover and directly manage the Pennix workflow lifecycle."""

from __future__ import annotations

import argparse
import hashlib
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

from adapters import codex_plugins, codex_static, skills_install, upstream
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


ACTION_NAMES = ("install", "configure", "upgrade", "uninstall", "verify")
ACTION_STATES = {"managed", "native-owner", "verify-only", "project-only", "not-applicable"}


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
    if not isinstance(value, dict) or value.get("schema") != 2 or not isinstance(components, dict) or not components:
        raise BootstrapError("catalog must contain schema 2 and non-empty components")
    for key, component in components.items():
        required = ("delivery", "source", "owner", "scope", "verify_key", "actions", "project_init")
        if not isinstance(component, dict) or any(name not in component for name in required):
            raise BootstrapError(f"catalog component is incomplete: {key}")
        actions = component["actions"]
        if (
            not isinstance(actions, dict)
            or set(actions) != set(ACTION_NAMES)
            or any(actions[name] not in ACTION_STATES for name in ACTION_NAMES)
        ):
            raise BootstrapError(f"catalog action capabilities are invalid: {key}")
        if component["project_init"] not in ACTION_STATES:
            raise BootstrapError(f"catalog project initialization capability is invalid: {key}")
        delivery = component["delivery"]
        if delivery not in {"package", "plugin", "native", "static", "source"}:
            raise BootstrapError(f"catalog delivery is invalid: {key}")
        if delivery in {"package", "plugin", "native"} and not isinstance(component.get("approved_version"), str):
            raise BootstrapError(f"catalog approved version is missing: {key}")
        if delivery == "static" and not isinstance(component.get("template"), dict):
            raise BootstrapError(f"catalog template contract is missing: {key}")
        if delivery == "static":
            template = component["template"]
            name = template.get("name")
            revision = template.get("revision")
            template_path = SKILL_ROOT / "templates" / name if isinstance(name, str) else None
            if (
                not isinstance(name, str)
                or not isinstance(revision, str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", revision)
                or template_path is None
                or not template_path.is_file()
                or "sha256:" + hashlib.sha256(template_path.read_bytes()).hexdigest() != revision
            ):
                raise BootstrapError(f"catalog template revision is invalid: {key}")
        if delivery == "source" and not isinstance(component.get("source_contract"), dict):
            raise BootstrapError(f"catalog source contract is missing: {key}")
        if delivery == "source":
            submodules = component["source_contract"].get("submodules")
            if (
                not isinstance(submodules, dict)
                or not submodules
                or any(
                    not isinstance(path, str)
                    or not isinstance(commit, str)
                    or not re.fullmatch(r"[0-9a-f]{40}", commit)
                    for path, commit in submodules.items()
                )
            ):
                raise BootstrapError(f"catalog source revision is invalid: {key}")
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
        replaces = component.get("replaces", [])
        if not isinstance(replaces, list) or not all(
            isinstance(name, str) and PACKAGE_NAME.fullmatch(name) for name in replaces
        ):
            raise BootstrapError(f"catalog replacement metadata is invalid: {key}")
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
    matches = VERSION_RE.findall(raw.replace("_", ""))
    return matches[-1] if matches else None


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
    return installed_npm_packages().get(package)


def installed_npm_packages() -> dict[str, str]:
    npm = shutil.which("npm")
    if not npm:
        return {}
    try:
        result = subprocess.run(
            [npm, "list", "--global", "--depth=0", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    try:
        dependencies = json.loads(result.stdout).get("dependencies", {})
    except (AttributeError, json.JSONDecodeError):
        return {}
    return {
        name: metadata["version"]
        for name, metadata in dependencies.items()
        if isinstance(name, str) and isinstance(metadata, dict) and isinstance(metadata.get("version"), str)
    }


def npm_global_root() -> Path | None:
    npm = shutil.which("npm")
    if not npm:
        return None
    try:
        result = subprocess.run(
            [npm, "root", "--global"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    root = (result.stdout or "").strip()
    return Path(root).resolve() if root else None


def npm_owner_for_command(command: str) -> str | None:
    root = npm_global_root()
    if root is None:
        return None
    try:
        relative = Path(command).resolve().relative_to(root)
    except (OSError, ValueError):
        return None
    parts = relative.parts
    if not parts:
        return None
    package_root = root / parts[0]
    if parts[0].startswith("@"):
        if len(parts) < 2:
            return None
        package_root = root / parts[0] / parts[1]
    try:
        metadata = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    name = metadata.get("name")
    return name if isinstance(name, str) and PACKAGE_NAME.fullmatch(name) else None


def package_command(component: dict[str, Any], command: list[str]) -> list[str]:
    if component.get("package", {}).get("source") != "npm":
        return command
    root = npm_global_root()
    if root is None:
        return command
    probe = root if root.exists() else root.parent
    return ["sudo", *command] if not os.access(probe, os.W_OK) else command


def probe_component(
    component: dict[str, Any],
    codex_home: Path | None = None,
    source: Path | None = None,
    destination: str | None = None,
) -> tuple[str, str | None]:
    adapter = component.get("adapter")
    if adapter == "codex-config":
        target = (codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))) / "config.toml"
        state = codex_static.config_state(codex_static.read(target))
        return {"current": "match", "seeded": "seeded", "absent": "missing"}.get(state, "drifted"), state
    if adapter == "codex-agents":
        target = (codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))) / "AGENTS.md"
        state = codex_static.template_state(target)
        return {"current": "match", "absent": "missing"}.get(state, "drifted"), state
    if adapter == "pennix-skills":
        if source is None:
            return "unknown", None
        try:
            expected = {name for name, _ in skills_install.discover_skills(source)}
            destination = skills_install.resolve_destination(destination)
        except skills_install.InstallError:
            return "unknown", None
        if not destination.exists():
            return "missing", None
        entries = {entry.name for entry in destination.iterdir()}
        if entries != expected or any(not (destination / name / "SKILL.md").is_file() for name in expected):
            return "drifted", None
        return "match", str(destination)
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
    if status == "match" and isinstance(package, dict):
        owner = (
            npm_owner_for_command(command)
            if package.get("source") == "npm"
            else installed_package_owner(command)
        )
        if owner is None and package.get("source") == "npm":
            status = "unknown"
        elif owner != package["name"]:
            status = "drifted"
    return status, observed


def discover(args: argparse.Namespace, catalog: dict[str, Any]) -> dict[str, Any]:
    components = {}
    for key, component in catalog["components"].items():
        status, observed = probe_component(
            component, args.codex_home, args.source, getattr(args, "destination", None)
        )
        package = component.get("package")
        command = shutil.which(str(component["probe"])) if component.get("probe") else None
        observed_package = None
        candidate_version = None
        target_package = None
        candidate_owner = None
        if isinstance(package, dict):
            target_package = package["name"]
            candidate_owner = package["source"]
            if package.get("source") == "npm":
                observed_package = npm_owner_for_command(command) if command else None
                if observed_package is None:
                    installed = installed_npm_packages()
                    for name in [target_package, *component.get("replaces", [])]:
                        if name in installed:
                            observed_package = name
                            break
            elif command:
                observed_package = installed_package_owner(command)
            host_info = host.detect_host()
            installer = host_info.get("installers", {}).get(package.get("source"))
            if isinstance(installer, str):
                candidate_version = package_candidate_version(installer, target_package, package.get("registry"))
        components[key] = {
            "status": status,
            "observed_version": observed,
            "catalog_version": component.get("approved_version"),
            "candidate_version": candidate_version,
            "owner": component["owner"],
            "scope": component["scope"],
            "verify_key": component["verify_key"],
            "delivery": component["delivery"],
            "actions": component["actions"],
            "project_init": component["project_init"],
            "observed_package": observed_package,
            "target_package": target_package,
            "candidate_owner": candidate_owner,
        }
    source = args.source
    source_ready = (source / "skills" / "pennix-workflow-lifecycle" / "SKILL.md").is_file()
    agents = args.codex_home / "AGENTS.md"
    config = args.codex_home / "config.toml"
    agents_state = codex_static.template_state(agents)
    config_state = codex_static.config_state(codex_static.read(config))
    return {
        "schema": 2,
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


def verify_inventory(args: argparse.Namespace, catalog: dict[str, Any], inventory: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, component in catalog["components"].items():
        observed = inventory["components"][key]
        if observed["status"] != "match":
            failures.append(f"{key}: observed status is {observed['status']}")
        if component["delivery"] == "source":
            try:
                source = skills_install.resolve_source(str(args.source))
                skills_install.ensure_submodules(
                    source,
                    initialize=False,
                    expected_commits=component["source_contract"]["submodules"],
                )
            except skills_install.InstallError as error:
                failures.append(f"{key}: {error}")
        if isinstance(component.get("upstream_inspection"), dict):
            try:
                evidence = upstream.inspect_component(component)
            except upstream.UpstreamInspectionError as error:
                evidence = {"status": "unavailable", "reason": str(error)}
            observed["upstream"] = evidence
            if evidence.get("status") != "match":
                failures.append(f"{key}: upstream inspection is {evidence.get('status')}")
    inventory["verification"] = {
        "status": "match" if not failures else "blocked",
        "failures": failures,
    }
    return failures


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
    if installer != "npm":
        version = re.search(r"(?m)^\s*Version\s*:\s*(\S+)", result.stdout)
        return normalize_version(version.group(1)) if version else None
    return normalize_version(result.stdout)


def inspect_for_operation(component: dict[str, Any]) -> None:
    if not isinstance(component.get("upstream_inspection"), dict):
        return
    try:
        evidence = upstream.inspect_component(component)
    except upstream.UpstreamInspectionError as error:
        raise BootstrapError(str(error)) from error
    if evidence.get("status") != "match":
        raise BootstrapError(f"upstream inspection blocked the component: {evidence.get('status')}")


def static_operation(args: argparse.Namespace, key: str, component: dict[str, Any], operation: str) -> str:
    adapter = component["adapter"]
    if adapter == "codex-config":
        path = args.codex_home / "config.toml"
        state = codex_static.config_state(codex_static.read(path))
        if operation == "uninstall":
            if state == "seeded":
                return "no-op"
            if state != "current":
                raise BootstrapError(f"refusing {state} lifecycle config: {path}")
            codex_static.remove_config_sections(path)
            return "changed"
        if state == "current":
            return "no-op"
        if state != "seeded":
            raise BootstrapError(f"refusing {state} lifecycle config: {path}")
        codex_static.apply_config(path)
        return "changed"

    if adapter == "codex-agents":
        path = args.codex_home / "AGENTS.md"
        state = codex_static.template_state(path)
        if operation == "uninstall":
            if state == "absent":
                return "no-op"
            if state != "current":
                raise BootstrapError(f"refusing {state} lifecycle template: {path}")
            path.unlink()
            return "changed"
        if state == "current":
            return "no-op"
        if state == "absent":
            if operation == "upgrade":
                raise BootstrapError("cannot upgrade an uninstalled AGENTS.md template")
            codex_static.apply_template(path)
            return "changed"
        raise BootstrapError(f"refusing {state} lifecycle template: {path}")

    source = skills_install.resolve_source(str(args.source))
    skills_install.ensure_submodules(
        source,
        initialize=operation != "uninstall",
        expected_commits=component.get("source_contract", {}).get("submodules"),
    )
    skills = skills_install.discover_skills(source)
    destination = skills_install.resolve_destination(args.destination)
    if operation == "uninstall":
        existed = destination.exists()
        skills_install.uninstall_skills(skills, destination)
        return "changed" if existed else "no-op"
    else:
        changed = skills_install.install_skills(skills, destination)
    return "changed" if operation == "uninstall" or changed else "no-op"


def component_operation(
    args: argparse.Namespace, catalog: dict[str, Any], key: str, component: dict[str, Any], operation: str
) -> str:
    if operation != "uninstall":
        inspect_for_operation(component)
    current_host = host.detect_host()
    if not current_host["supported"]:
        raise BootstrapError(str(current_host["reason"]))
    status, _ = probe_component(component, args.codex_home, getattr(args, "source", None))
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
            if probe_component(component, args.codex_home, getattr(args, "source", None))[0] != "missing":
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
        if metadata.get("source") != "npm":
            if command and installed_package_owner(command) != package_name:
                raise BootstrapError(f"{key} is not owned by {package_name}")
        elif package_name not in installed_npm_packages():
            raise BootstrapError(f"{key} is not owned by {package_name}")
        try:
            result = subprocess.run(
                package_command(metadata, host.package_remove_command(installer, package_name)),
                check=False,
            )
        except (OSError, ValueError) as error:
            raise BootstrapError(f"package manager could not start: {error}") from error
        if result.returncode:
            raise BootstrapError(f"package manager failed ({result.returncode})")
        if probe_component(component, args.codex_home, getattr(args, "source", None))[0] != "missing":
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
        replacements = component.get("replaces", [])
        replacement_owner = None
        if metadata.get("source") == "npm":
            installed = installed_npm_packages()
            replacement_owner = next((name for name in replacements if name in installed), None)
            if command:
                command_owner = npm_owner_for_command(command)
                if command_owner not in {None, package_name, *replacements}:
                    raise BootstrapError(f"installed command is owned by unmanaged npm package {command_owner}")
                if command_owner is None and package_name not in installed and replacement_owner is None:
                    raise BootstrapError("installed command has no verifiable npm owner")
        elif command:
            command_owner = installed_package_owner(command)
            if command_owner in component.get("conflicts", []):
                raise BootstrapError("installed command is owned by a conflicting package")
            replacement_owner = command_owner if command_owner in replacements else None
            if command_owner is None and status != "missing":
                raise BootstrapError("installed command has no verifiable package owner")
            if command_owner not in {None, package_name, *replacements}:
                raise BootstrapError(f"installed command is owned by unmanaged package {command_owner}")
        expected = normalize_version(str(component["approved_version"]))
        if (
            metadata.get("source") == "npm"
            and status != "match"
            and normalize_version(installed_npm_version(package_name) or "") == expected
        ):
            raise BootstrapError("installed npm package does not provide an effective matching command")
        if package_candidate_version(installer, package_name, registry) != expected:
            raise BootstrapError("repository candidate does not match catalog")
        if replacement_owner:
            try:
                result = subprocess.run(
                    package_command(metadata, host.package_remove_command(installer, replacement_owner)),
                    check=False,
                )
            except (OSError, ValueError) as error:
                raise BootstrapError(f"package manager could not remove replacement owner: {error}") from error
            if result.returncode:
                raise BootstrapError(f"replacement owner removal failed ({result.returncode})")
        install_name = f"{package_name}@{expected}" if metadata.get("source") == "npm" else package_name
        try:
            result = subprocess.run(
                package_command(metadata, host.package_install_command(installer, install_name, registry)),
                check=False,
            )
        except (OSError, ValueError) as error:
            raise BootstrapError(f"package manager could not start: {error}") from error
        if result.returncode:
            raise BootstrapError(f"package manager failed ({result.returncode})")
    if probe_component(component, args.codex_home, getattr(args, "source", None))[0] != "match":
        raise BootstrapError(f"{operation} postcondition failed: {key} does not match catalog")
    return "changed"


def run_lifecycle(args: argparse.Namespace, catalog: dict[str, Any]) -> None:
    if not args.component:
        raise BootstrapError(f"{args.command} requires --component")
    if not args.yes:
        raise BootstrapError(f"{args.command} requires --yes")
    component = args.component
    if component not in catalog["components"]:
        raise BootstrapError(f"unknown lifecycle component: {component}")
    metadata = catalog["components"][component]
    capability = metadata["actions"][args.command]
    if capability != "managed":
        reason = metadata.get("native_owner_reason", f"{component} action is {capability}")
        raise BootstrapError(f"{component} {args.command} is {capability}: {reason}")
    current_host = host.detect_host()
    if not current_host["supported"]:
        raise BootstrapError(str(current_host["reason"]))
    if metadata["delivery"] in {"static", "source"}:
        status = static_operation(args, component, metadata, args.command)
    else:
        status = component_operation(args, catalog, component, metadata, args.command)
    print(json.dumps({"operation": args.command, "component": component, "status": status}, ensure_ascii=False))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", *ACTION_NAMES))
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
        if args.command == "discover":
            print(json.dumps(inventory, ensure_ascii=False, indent=2))
        elif args.command == "verify":
            failures = verify_inventory(args, catalog, inventory)
            print(json.dumps(inventory, ensure_ascii=False, indent=2))
            if failures:
                print("error: verification blocked: " + "; ".join(failures), file=sys.stderr)
                return 2
        else:
            run_lifecycle(args, catalog)
        return 0
    except (BootstrapError, codex_static.StaticError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
