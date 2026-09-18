#!/usr/bin/env python3
"""Discover, plan, and explicitly apply the Pennix workflow baseline."""

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
PROJECT_ACTIONS = (
    ("trellis-project", "trellis", "project", "native workflow init/update/selection"),
    ("codegraph-project", "codegraph", "project", "project config/index initialization"),
    ("aoe-project", "aoe", "project", "project session initialization"),
)


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


def action(
    action_id: str,
    owner: str,
    scope: str,
    target: str,
    status: str,
    mode: str,
    source: str | None = None,
    approved_version: str | None = None,
    blocked_reason: str | None = None,
    package: dict[str, str] | None = None,
    plugin: dict[str, Any] | None = None,
    upstream_inspection: dict[str, Any] | None = None,
    decision_profile: dict[str, Any] | None = None,
    category: str = "system-installation",
) -> dict[str, Any]:
    result = {
        "id": action_id,
        "owner": owner,
        "scope": scope,
        "target": target,
        "status": status,
        "mode": mode,
        "category": category,
        "risk": "high" if scope == "global" else "medium",
        "confirmation": "required",
        "precondition": "catalog and owner verification are available",
        "postcondition": "fresh discover reports the expected state",
        "rollback": "bootstrap receipt/hash or native owner",
    }
    if source is not None:
        result["source"] = source
    if approved_version is not None:
        result["approved_version"] = approved_version
    if blocked_reason is not None:
        result["blocked_reason"] = blocked_reason
    if package is not None:
        result["package"] = package
    if plugin is not None:
        result["plugin"] = plugin
    if upstream_inspection is not None:
        result["upstream_inspection"] = upstream_inspection
    if decision_profile is not None:
        result["decision_profile"] = decision_profile
    return result


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


def package_action_mode(
    component: dict[str, Any],
    host_state: dict[str, Any],
    current_status: str | None = None,
    observed_package: str | None = None,
) -> tuple[str, str | None, dict[str, str] | None]:
    package = component.get("package")
    if not isinstance(package, dict):
        reason = component.get("native_owner_reason", "component requires a native owner adapter")
        return "plan-only", str(reason), None
    installer = host_state["installers"].get(package["source"])
    if not isinstance(installer, str):
        return "blocked", f"no available {package['source']} package installer", None
    observed = package_candidate_version(installer, package["name"], package.get("registry"))
    expected = normalize_version(str(component["approved_version"]))
    if observed != expected:
        return "blocked", "repository candidate does not match catalog", None
    if observed_package in component.get("conflicts", []):
        return "blocked", f"installed command is owned by conflicting package: {observed_package}", None
    if (
        package["source"] == "npm"
        and current_status != "match"
        and normalize_version(installed_npm_version(package["name"]) or "") == expected
    ):
        return "blocked", "installed npm package does not provide an effective matching command", None
    return "applyable", None, {
        "name": package["name"],
        "source": package["source"],
        "installer": installer,
        **({"registry": package["registry"]} if package.get("registry") else {}),
    }


def plugin_action_mode(
    component: dict[str, Any], inventory: dict[str, Any], codex_home: Path
) -> tuple[str, str | None, dict[str, Any] | None]:
    codex = inventory["components"].get("codex-cli", {})
    if codex.get("status") != "match":
        return "blocked", "Codex CLI does not match catalog", None
    plugin = component.get("plugin")
    if not isinstance(plugin, dict):
        return "plan-only", "component requires a native owner adapter", None
    marketplace = plugin["marketplace"]
    try:
        state = codex_plugins.marketplace_status(codex_home, marketplace["name"], marketplace["source"])
    except codex_plugins.PluginError as error:
        return "blocked", str(error), None
    if state != "absent":
        return "blocked", f"existing marketplace cannot be ref-verified: {state}", None
    return "applyable", None, plugin


def inspect_upstream(component: dict[str, Any], enabled: bool) -> dict[str, Any] | None:
    if not isinstance(component.get("upstream_inspection"), dict):
        return None
    if not enabled:
        return {
            "status": "inspection-required",
            "reason": "run plan with --inspect-upstream before selecting this component",
        }
    try:
        return upstream.inspect_component(component)
    except upstream.UpstreamInspectionError as error:
        return {"status": "unavailable", "reason": str(error)}


def plan(args: argparse.Namespace, inventory: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    agents_state = inventory["static"]["agents_template"]
    agents_mode = {"absent": "applyable", "current": "no-op"}.get(agents_state, "plan-only")
    config_state = inventory["static"]["config_install"]
    config_mode = {"seeded": "applyable", "current": "no-op"}.get(config_state, "blocked")
    source_ready = inventory["source"]["ready"]
    host_state = inventory["host"]
    host_supported = bool(host_state["supported"])
    host_reason = host_state["reason"]
    if not host_supported:
        agents_mode = "blocked"
        config_mode = "blocked"
    actions = [
        action(
            "codex-config-install",
            "pennix-workflow-bootstrap",
            "global",
            inventory["static"]["config_path"],
            config_state,
            config_mode,
            blocked_reason=None if host_supported else str(host_reason),
        ),
        action(
            "codex-agents-install",
            "pennix-workflow-bootstrap",
            "global",
            inventory["static"]["agents_path"],
            agents_state,
            agents_mode,
            blocked_reason=None if host_supported else str(host_reason),
        ),
        action(
            "skills-install",
            "pennix-skills",
            "global",
            inventory["source"]["path"],
            "ready" if source_ready else "blocked",
            "applyable" if source_ready and host_supported else "blocked",
            blocked_reason=None if host_supported else str(host_reason),
        ),
    ]
    for key, state in inventory["components"].items():
        if state["status"] == "match":
            continue
        component = catalog["components"][key]
        inspection = inspect_upstream(component, bool(getattr(args, "inspect_upstream", False)))
        if inspection is not None and inspection["status"] != "match":
            mode, blocked_reason, package, plugin = "blocked", str(inspection["status"]), None, None
        elif isinstance(component.get("plugin"), dict):
            mode, blocked_reason, plugin = plugin_action_mode(component, inventory, args.codex_home)
            package = None
        else:
            mode, blocked_reason, package = package_action_mode(
                component, host_state, state["status"], state.get("observed_package")
            )
            plugin = None
        if not host_supported:
            mode = "blocked"
            blocked_reason = str(host_reason)
        actions.append(
            action(
                f"component:{key}",
                component["owner"],
                component["scope"],
                key,
                state["status"],
                mode,
                component["source"],
                str(component["approved_version"]),
                blocked_reason=blocked_reason,
                package=package,
                plugin=plugin,
                upstream_inspection=inspection,
                decision_profile=component.get("decision_profile"),
            )
        )
    project_target = str(args.project_root) if args.project_root else "<explicit --project-root required>"
    project_mode = "plan-only" if host_supported and args.project_root else "blocked"
    project_reason = None if host_supported and args.project_root else (
        "project initialization requires explicit --project-root"
        if host_supported
        else str(host_reason)
    )
    for action_id, owner, scope, target in PROJECT_ACTIONS:
        actions.append(
            action(
                action_id,
                owner,
                scope,
                project_target,
                "optional",
                project_mode,
                blocked_reason=project_reason,
                category="project-initialize",
            )
        )
    return {
        "schema": 1,
        "planned_at": now(),
        "inventory": inventory,
        "upstream_inspection_requested": bool(getattr(args, "inspect_upstream", False)),
        "actions": actions,
    }


def state_dir(args: argparse.Namespace) -> Path:
    return args.state_dir or args.codex_home / ".pennix-workflow-bootstrap"


def write_receipt(args: argparse.Namespace, receipt: dict[str, Any]) -> Path:
    directory = state_dir(args) / "receipts"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{receipt['created_at'].replace(':', '').replace('.', '')}-{receipt['action']}.json"
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def backup_file(args: argparse.Namespace, path: Path, contents: str) -> Path | None:
    if not path.exists():
        return None
    directory = state_dir(args) / "backups"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{path.name}.{now().replace(':', '').replace('.', '')}.bak"
    target.write_text(contents, encoding="utf-8")
    os.chmod(target, 0o600)
    return target


def apply_action(args: argparse.Namespace, catalog: dict[str, Any]) -> None:
    if not args.yes:
        raise BootstrapError("apply requires --yes after reviewing the named action")
    current_host = host.detect_host()
    if not current_host["supported"]:
        raise BootstrapError(str(current_host["reason"]))
    if args.action in {"codex-config-install", "codex-agents-install"}:
        if args.action == "codex-config-install":
            path = args.codex_home / "config.toml"
            before = codex_static.read(path)
            before_exists = path.exists()
            if codex_static.config_state(before) not in {"seeded", "current"}:
                raise BootstrapError(f"refusing {codex_static.config_state(before)} bootstrap config: {path}")
            backup = backup_file(args, path, before)
            _, after = codex_static.apply_config(path)
        else:
            path = args.codex_home / "AGENTS.md"
            before = codex_static.read(path)
            before_exists = path.exists()
            if codex_static.template_state(path) not in {"absent", "current"}:
                raise BootstrapError(f"refusing {codex_static.template_state(path)} bootstrap template: {path}")
            backup = backup_file(args, path, before)
            _, after = codex_static.apply_template(path)
        receipt = {
            "schema": 1,
            "action": args.action,
            "created_at": now(),
            "target": str(path),
            "before_hash": codex_static.digest(before),
            "after_hash": codex_static.digest(after),
            "before_exists": before_exists,
            "backup": str(backup) if backup else None,
            "rollback": "restore bootstrap backup or remove newly created file",
        }
    elif args.action == "codex-agents-marker":
        raise BootstrapError("codex-agents-marker is retired; use codex-agents-install")
    elif args.action == "skills-install":
        if not args.source.exists():
            raise BootstrapError(f"source checkout is not ready: {args.source}")
        from adapters import skills_install

        source = skills_install.resolve_source(str(args.source))
        skills_install.ensure_submodules(source, initialize=True)
        skills = skills_install.discover_skills(source)
        destination = skills_install.resolve_destination(args.destination)
        skills_install.install_skills(skills, destination)
        receipt = {
            "schema": 1,
            "action": args.action,
            "created_at": now(),
            "target": str(destination),
            "source": str(source),
            "rollback": "native source reinstall",
        }
    elif args.action.startswith("component:"):
        key = args.action.removeprefix("component:")
        component = catalog["components"].get(key)
        if not isinstance(component, dict):
            raise BootstrapError(f"unknown component action: {args.action}")
        if isinstance(component.get("upstream_inspection"), dict):
            digest = args.upstream_inspection_digest
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise BootstrapError(
                    "component requires the SHA-256 from a reviewed plan --inspect-upstream result"
                )
        plugin = component.get("plugin")
        if isinstance(plugin, dict):
            codex_component = catalog["components"].get("codex-cli")
            if not isinstance(codex_component, dict) or probe_component(codex_component, args.codex_home)[0] != "match":
                raise BootstrapError("Codex CLI does not match catalog")
            marketplace = plugin["marketplace"]
            try:
                state = codex_plugins.marketplace_status(
                    args.codex_home, marketplace["name"], marketplace["source"]
                )
                if state != "absent":
                    raise BootstrapError(f"existing marketplace cannot be ref-verified: {state}")
                codex_plugins.install_plugin(args.codex_home, plugin)
            except codex_plugins.PluginError as error:
                raise BootstrapError(str(error)) from error
            if probe_component(component, args.codex_home)[0] != "match":
                raise BootstrapError("Codex plugin install postcondition failed")
            receipt = {
                "schema": 1,
                "action": args.action,
                "created_at": now(),
                "target": plugin,
                "rollback": "Codex native plugin lifecycle; automatic removal is unsafe",
            }
        else:
            metadata = component.get("package") if isinstance(component.get("package"), dict) else {}
            installer = current_host["installers"].get(metadata.get("source"))
            package_name = metadata.get("name")
            registry = metadata.get("registry")
            if not isinstance(installer, str) or not isinstance(package_name, str):
                raise BootstrapError(f"component has no supported package action: {key}")
            command = shutil.which(str(component["probe"])) if component.get("probe") else None
            if command and installed_package_owner(command) in component.get("conflicts", []):
                raise BootstrapError("installed command is owned by a conflicting package")
            expected = normalize_version(str(component["approved_version"]))
            if package_candidate_version(installer, package_name, registry) != expected:
                raise BootstrapError("repository candidate does not match catalog")
            install_name = f"{package_name}@{expected}" if metadata.get("source") == "npm" else package_name
            try:
                result = subprocess.run(host.package_install_command(installer, install_name, registry), check=False)
            except (OSError, ValueError) as error:
                raise BootstrapError(f"package manager could not start: {error}") from error
            if result.returncode:
                raise BootstrapError(f"package manager failed ({result.returncode})")
            status, _ = probe_component(component, args.codex_home)
            owner = (
                installed_package_owner(shutil.which(str(component["probe"])))
                if metadata.get("source") != "npm" and component.get("probe") and shutil.which(str(component["probe"]))
                else None
            )
            if status != "match" or (metadata.get("source") != "npm" and owner != package_name):
                raise BootstrapError("package install postcondition failed: component does not match catalog")
            receipt = {
                "schema": 1,
                "action": args.action,
                "created_at": now(),
                "target": metadata,
                "package_manager": installer,
                "rollback": "native package manager; automatic removal is unsafe",
            }
        if isinstance(component.get("upstream_inspection"), dict):
            receipt["upstream_inspection_sha256"] = args.upstream_inspection_digest
    else:
        raise BootstrapError(f"action is plan-only or unknown: {args.action}")
    print(json.dumps({"applied": args.action, "receipt": str(write_receipt(args, receipt))}, ensure_ascii=False))


def rollback(args: argparse.Namespace) -> None:
    receipt_path = args.receipt.resolve()
    root = state_dir(args).resolve() / "receipts"
    if root not in receipt_path.parents:
        raise BootstrapError("receipt must belong to this bootstrap state directory")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BootstrapError(f"invalid receipt: {receipt_path}") from error
    if receipt.get("action") not in {"codex-config-install", "codex-agents-install"}:
        raise BootstrapError("only bootstrap template receipts support automatic rollback")
    path = Path(receipt["target"])
    current = codex_static.read(path)
    if codex_static.digest(current) != receipt.get("after_hash"):
        raise BootstrapError("target hash differs from receipt; refusing rollback")
    if receipt.get("before_exists", False):
        backup = receipt.get("backup")
        backup_path = Path(backup).resolve() if isinstance(backup, str) else None
        backup_root = (state_dir(args) / "backups").resolve()
        if backup_path is None or backup_root not in backup_path.parents:
            raise BootstrapError("receipt backup is missing or outside the bootstrap state directory")
        try:
            before = backup_path.read_text(encoding="utf-8")
        except OSError as error:
            raise BootstrapError(f"cannot read rollback backup: {backup_path}") from error
        codex_static.write(path, before)
        if codex_static.digest(codex_static.read(path)) != receipt.get("before_hash"):
            raise BootstrapError("rollback postcondition failed: before hash differs")
    else:
        if path.is_symlink():
            raise BootstrapError(f"refusing symbolic-link rollback target: {path}")
        path.unlink(missing_ok=True)
    print(json.dumps({"rolled_back": str(receipt_path), "target": str(path)}, ensure_ascii=False))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", "plan", "apply", "verify", "rollback"))
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--source", type=Path, default=SCRIPT_ROOT.parents[2])
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--destination")
    parser.add_argument("--action")
    parser.add_argument("--inspect-upstream", action="store_true")
    parser.add_argument("--upstream-inspection-digest")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        args.catalog = args.catalog.expanduser().resolve()
        # Preserve symlink information so codex_static can reject unsafe targets.
        args.codex_home = args.codex_home.expanduser().absolute()
        if args.project_root:
            args.project_root = args.project_root.expanduser().resolve()
        args.source = args.source.expanduser().resolve()
        if args.state_dir:
            args.state_dir = args.state_dir.expanduser().absolute()
        if args.command == "rollback":
            if not args.receipt:
                raise BootstrapError("rollback requires --receipt")
            rollback(args)
            return 0
        catalog = load_catalog(args.catalog)
        inventory = discover(args, catalog)
        if args.command in {"discover", "verify"}:
            print(json.dumps(inventory, ensure_ascii=False, indent=2))
        elif args.command == "plan":
            print(json.dumps(plan(args, inventory, catalog), ensure_ascii=False, indent=2))
        else:
            if not args.action:
                raise BootstrapError("apply requires --action")
            apply_action(args, catalog)
        return 0
    except (BootstrapError, codex_static.StaticError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
