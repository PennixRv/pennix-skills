from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import bootstrap
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
    def inventory(self) -> dict[str, object]:
        return {
            "static": {
                "agents_path": "/tmp/AGENTS.md",
                "agents_template": "current",
                "config_path": "/tmp/config.toml",
                "config_install": "current",
            },
            "source": {"path": "/tmp/source", "ready": True},
            "host": {"supported": True, "reason": None, "installers": {"aur": "yay"}},
            "components": {"aoe": {"status": "missing"}},
        }

    def test_known_upstream_control_surface_is_recorded(self) -> None:
        inspected = upstream.inspect_component(AOE_COMPONENT, lambda _: CURRENT_INSTALLER)
        self.assertEqual(inspected["status"], "match")
        self.assertEqual(inspected["semantics"]["configurable_environment"], ["INSTALL_DIR"])
        self.assertEqual(len(inspected["sha256"]), 64)

    def test_new_upstream_control_surface_blocks_the_plan(self) -> None:
        changed = CURRENT_INSTALLER.replace(
            'INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"',
            'INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"\nAOE_COLOR="${AOE_COLOR:-auto}"',
        )
        inspected = upstream.inspect_component(AOE_COMPONENT, lambda _: changed)
        self.assertEqual(inspected["status"], "upstream-contract-changed")
        self.assertIn("AOE_COLOR", inspected["reason"])

    def test_command_line_option_parsing_blocks_the_plan(self) -> None:
        changed = CURRENT_INSTALLER.replace(
            'main "$@"',
            'case "$1" in --quiet) quiet=true ;; esac\nmain "$@"',
        )
        inspected = upstream.inspect_component(AOE_COMPONENT, lambda _: changed)
        self.assertEqual(inspected["status"], "upstream-contract-changed")
        self.assertIn("command-line argument handling", inspected["reason"])

    def test_plan_requires_explicit_inspection_and_preserves_its_result(self) -> None:
        catalog = {"components": {"aoe": AOE_COMPONENT}}
        no_inspection = bootstrap.plan(
            argparse.Namespace(project_root=None, inspect_upstream=False), self.inventory(), catalog
        )
        action = next(item for item in no_inspection["actions"] if item["id"] == "component:aoe")
        self.assertEqual(action["mode"], "blocked")
        self.assertEqual(action["blocked_reason"], "inspection-required")

        evidence = upstream.inspect_component(AOE_COMPONENT, lambda _: CURRENT_INSTALLER)
        with (
            patch.object(bootstrap.upstream, "inspect_component", return_value=evidence),
            patch.object(
                bootstrap,
                "package_action_mode",
                return_value=("applyable", None, {"name": "agent-of-empires-bin", "source": "aur", "installer": "yay"}),
            ),
        ):
            inspected_plan = bootstrap.plan(
                argparse.Namespace(project_root=None, inspect_upstream=True), self.inventory(), catalog
            )
        action = next(item for item in inspected_plan["actions"] if item["id"] == "component:aoe")
        self.assertEqual(action["mode"], "applyable")
        self.assertEqual(action["upstream_inspection"]["sha256"], evidence["sha256"])
        self.assertEqual(action["decision_profile"], AOE_COMPONENT["decision_profile"])

    def test_apply_never_inspects_upstream_and_requires_reviewed_digest(self) -> None:
        args = argparse.Namespace(yes=True, action="component:aoe", upstream_inspection_digest=None)
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"supported": True}),
            patch.object(bootstrap.upstream, "inspect_component") as inspect,
            self.assertRaisesRegex(bootstrap.BootstrapError, "requires the SHA-256"),
        ):
            bootstrap.apply_action(args, {"components": {"aoe": AOE_COMPONENT}})
        inspect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
