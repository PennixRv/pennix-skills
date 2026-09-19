from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import lifecycle as bootstrap
from adapters import upstream


AOE_COMPONENT = {
    "approved_version": "1.2.3",
    "source": "fixture",
    "owner": "aoe",
    "scope": "global/project",
    "verify_key": "aoe --version",
    "probe": "aoe",
    "version_args": ["--version"],
    "package": {"source": "aur", "name": "agent-of-empires-bin"},
    "upstream_inspection": {
        "url": "https://example.test/install.sh",
        "parser": "aoe-install-sh-v1",
        "allowed_configurable_environment": ["INSTALL_DIR"],
        "on_contract_change": "block",
    },
    "decision_profile": {"automatic": [], "questions": []},
}

CURRENT_INSTALLER = """#!/bin/bash
DEFAULT_INSTALL_DIR="$HOME/.local/bin"
INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
info() { printf '%s\\n' "$1"; }
get_latest_version() {
  curl -fsSL "https://api.github.com/repos/agent-of-empires/agent-of-empires/releases/latest"
}
main "$@"
"""


class UpstreamInspectionTests(unittest.TestCase):
    def test_known_upstream_control_surface_is_recorded(self) -> None:
        inspected = upstream.inspect_component(AOE_COMPONENT, lambda _: CURRENT_INSTALLER)
        self.assertEqual(inspected["status"], "match")
        self.assertEqual(inspected["semantics"]["configurable_environment"], ["INSTALL_DIR"])
        self.assertEqual(len(inspected["sha256"]), 64)

    def test_new_upstream_control_surface_blocks_the_operation(self) -> None:
        changed = CURRENT_INSTALLER.replace(
            'INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"',
            'INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"\nAOE_COLOR="${AOE_COLOR:-auto}"',
        )
        inspected = upstream.inspect_component(AOE_COMPONENT, lambda _: changed)
        self.assertEqual(inspected["status"], "upstream-contract-changed")
        self.assertIn("AOE_COLOR", inspected["reason"])

    def test_changed_upstream_hash_blocks_even_when_control_surface_matches(self) -> None:
        component = {
            **AOE_COMPONENT,
            "upstream_inspection": {
                **AOE_COMPONENT["upstream_inspection"],
                "expected_sha256": "0" * 64,
            },
        }
        inspected = upstream.inspect_component(component, lambda _: CURRENT_INSTALLER)
        self.assertEqual(inspected["status"], "upstream-contract-changed")
        self.assertIn("hash changed", inspected["reason"])

    def test_command_line_option_parsing_blocks_the_operation(self) -> None:
        changed = CURRENT_INSTALLER.replace(
            'main "$@"',
            'case "$1" in --quiet) quiet=true ;; esac\nmain "$@"',
        )
        inspected = upstream.inspect_component(AOE_COMPONENT, lambda _: changed)
        self.assertEqual(inspected["status"], "upstream-contract-changed")
        self.assertIn("command-line argument handling", inspected["reason"])

    def test_install_inspects_upstream_before_using_the_native_owner(self) -> None:
        evidence = upstream.inspect_component(AOE_COMPONENT, lambda _: CURRENT_INSTALLER)
        args = SimpleNamespace(codex_home=Path("/tmp/codex"))
        with (
            patch.object(bootstrap.upstream, "inspect_component", return_value=evidence),
            patch.object(bootstrap.host, "detect_host", return_value={"supported": True, "installers": {"aur": "yay"}}),
            patch.object(bootstrap, "probe_component", side_effect=[("missing", None), ("match", "1.2.3")]),
            patch.object(bootstrap, "package_candidate_version", return_value="1.2.3"),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/aoe"),
            patch.object(bootstrap, "installed_package_owner", return_value="agent-of-empires-bin"),
            patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)),
        ):
            self.assertEqual(
                bootstrap.component_operation(args, {"components": {}}, "aoe", AOE_COMPONENT, "install"),
                "changed",
            )

    def test_changed_upstream_contract_stops_before_package_manager(self) -> None:
        args = SimpleNamespace(codex_home=Path("/tmp/codex"))
        with (
            patch.object(
                bootstrap.upstream,
                "inspect_component",
                return_value={"status": "upstream-contract-changed"},
            ),
            patch.object(bootstrap.subprocess, "run") as run,
            self.assertRaisesRegex(bootstrap.BootstrapError, "upstream inspection blocked"),
        ):
            bootstrap.component_operation(args, {"components": {}}, "aoe", AOE_COMPONENT, "install")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
