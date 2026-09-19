from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "bootstrap.py"
SOURCE_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(SCRIPT.parent))

import bootstrap


class BootstrapTests(unittest.TestCase):
    def catalog(self, root: Path) -> Path:
        catalog = root / "catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "components": {
                        "fixture": {
                            "approved_version": "1.2.3",
                            "source": "fixture",
                            "owner": "test",
                            "scope": "global",
                            "verify_key": "fixture --version",
                            "probe": "fixture",
                            "version_args": ["--version"],
                            "package": {"source": "official", "name": "fixture-package"},
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        return catalog

    def run_cli(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--catalog",
                str(self.catalog(root)),
                "--codex-home",
                str(root / "codex"),
                "--source",
                str(SOURCE_ROOT),
                *arguments,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_discover_and_verify_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for command in ("discover", "verify"):
                result = self.run_cli(root, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("components", json.loads(result.stdout))
            self.assertFalse((root / "codex").exists())

    def test_removed_orchestration_commands_are_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cli(Path(temporary), "plan")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)

    def test_lifecycle_requires_component_and_confirmation(self) -> None:
        catalog = {"components": {}}
        args = SimpleNamespace(command="install", component=None, yes=False)
        with self.assertRaisesRegex(bootstrap.BootstrapError, "requires --component"):
            bootstrap.run_lifecycle(args, catalog)
        args.component = "codex-agents"
        with self.assertRaisesRegex(bootstrap.BootstrapError, "requires --yes"):
            bootstrap.run_lifecycle(args, catalog)

    def test_static_install_upgrade_and_uninstall_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "codex"
            home.mkdir()
            config = home / "config.toml"
            config.write_text(bootstrap.codex_static.seed_config("https://api.example.test/v1"), encoding="utf-8")
            args = SimpleNamespace(codex_home=home, source=SOURCE_ROOT, destination=None)

            self.assertEqual(bootstrap.static_operation(args, "codex-config", "install"), "changed")
            self.assertEqual(bootstrap.static_operation(args, "codex-config", "upgrade"), "no-op")
            self.assertEqual(bootstrap.static_operation(args, "codex-config", "uninstall"), "changed")
            self.assertEqual(bootstrap.codex_static.config_state(config.read_text(encoding="utf-8")), "seeded")

            self.assertEqual(bootstrap.static_operation(args, "codex-agents", "install"), "changed")
            self.assertEqual(bootstrap.static_operation(args, "codex-agents", "uninstall"), "changed")
            self.assertEqual(bootstrap.static_operation(args, "codex-agents", "uninstall"), "no-op")

    def test_static_uninstall_refuses_drifted_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            target = home / "AGENTS.md"
            target.write_text("# user instructions\n", encoding="utf-8")
            args = SimpleNamespace(codex_home=home, source=SOURCE_ROOT, destination=None)
            with self.assertRaisesRegex(bootstrap.BootstrapError, "refusing drifted"):
                bootstrap.static_operation(args, "codex-agents", "uninstall")
            self.assertTrue(target.exists())

    def test_component_upgrade_and_uninstall_use_the_native_owner(self) -> None:
        component = {
            "approved_version": "1.2.3",
            "source": "fixture",
            "owner": "test",
            "scope": "global",
            "verify_key": "fixture --version",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "official", "name": "fixture-package"},
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"))
        host_state = {"supported": True, "installers": {"official": "pacman"}}
        with (
            patch.object(bootstrap.host, "detect_host", return_value=host_state),
            patch.object(bootstrap, "probe_component", side_effect=[("drifted", "1.0.0"), ("match", "1.2.3")]),
            patch.object(bootstrap, "package_candidate_version", return_value="1.2.3"),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
            patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run,
        ):
            self.assertEqual(
                bootstrap.component_operation(args, {"components": {}}, "fixture", component, "upgrade"),
                "changed",
            )
        self.assertEqual(run.call_args.args[0], ["sudo", "pacman", "-S", "--needed", "fixture-package"])

        with (
            patch.object(bootstrap.host, "detect_host", return_value=host_state),
            patch.object(bootstrap, "probe_component", side_effect=[("drifted", "1.0.0"), ("missing", None)]),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
            patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run,
        ):
            self.assertEqual(
                bootstrap.component_operation(args, {"components": {}}, "fixture", component, "uninstall"),
                "changed",
            )
        self.assertEqual(run.call_args.args[0], ["sudo", "pacman", "-R", "fixture-package"])

    def test_component_operation_refuses_an_unknown_state(self) -> None:
        component = {
            "approved_version": "1.2.3",
            "package": {"source": "official", "name": "fixture-package"},
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"))
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"supported": True, "installers": {}}),
            patch.object(bootstrap, "probe_component", return_value=("unknown", None)),
            self.assertRaisesRegex(bootstrap.BootstrapError, "cannot safely identify"),
        ):
            bootstrap.component_operation(args, {"components": {}}, "fixture", component, "uninstall")

    def test_default_catalog_accepts_scoped_npm_packages(self) -> None:
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        self.assertEqual(catalog["components"]["fastctx"]["package"]["name"], "@pennixrv/fastctx")
        self.assertEqual(catalog["components"]["ponytail-plugin"]["plugin"]["id"], "ponytail@ponytail")


if __name__ == "__main__":
    unittest.main()
