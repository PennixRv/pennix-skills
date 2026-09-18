from __future__ import annotations

import json
import argparse
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


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
                            "verify_key": "python probe",
                            "probe": sys.executable,
                            "version_args": ["-c", "print('fixture 1.2.3')"],
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

    def test_discover_and_plan_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            discovered = self.run_cli(root, "discover")
            self.assertEqual(discovered.returncode, 0, discovered.stderr)
            inventory = json.loads(discovered.stdout)
            self.assertEqual(inventory["components"]["fixture"]["status"], "match")
            planned = self.run_cli(root, "plan")
            self.assertEqual(planned.returncode, 0, planned.stderr)
            plan = json.loads(planned.stdout)
            trellis = next(item for item in plan["actions"] if item["id"] == "trellis-project")
            self.assertEqual(trellis["mode"], "blocked")
            self.assertIn("explicit --project-root", trellis["blocked_reason"])
            self.assertFalse((root / "codex").exists())

            planned_project = self.run_cli(root, "--project-root", str(root / "project"), "plan")
            self.assertEqual(planned_project.returncode, 0, planned_project.stderr)
            trellis = next(
                item for item in json.loads(planned_project.stdout)["actions"] if item["id"] == "trellis-project"
            )
            self.assertEqual(trellis["mode"], "plan-only")
            self.assertEqual(trellis["category"], "project-initialize")

    def test_apply_requires_named_confirmation_and_rolls_back_agents_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            denied = self.run_cli(root, "apply", "--action", "codex-agents-install")
            self.assertNotEqual(denied.returncode, 0)
            agents = root / "codex" / "AGENTS.md"
            self.assertFalse(agents.exists())

            applied = self.run_cli(
                root,
                "--state-dir",
                str(root / "state"),
                "apply",
                "--action",
                "codex-agents-install",
                "--yes",
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            receipt = Path(json.loads(applied.stdout)["receipt"])
            self.assertTrue(agents.exists())

            rolled_back = self.run_cli(
                root,
                "--state-dir",
                str(root / "state"),
                "rollback",
                "--receipt",
                str(receipt),
            )
            self.assertEqual(rolled_back.returncode, 0, rolled_back.stderr)
            self.assertFalse(agents.exists())

    def test_plan_only_action_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cli(Path(temporary), "apply", "--action", "trellis-project", "--yes")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("plan-only", result.stderr)

    def test_drifted_agents_template_is_plan_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            agents = root / "codex" / "AGENTS.md"
            agents.parent.mkdir()
            agents.write_text("# unrelated user instructions\n", encoding="utf-8")
            planned = self.run_cli(root, "plan")
            self.assertEqual(planned.returncode, 0, planned.stderr)
            template_action = next(
                item for item in json.loads(planned.stdout)["actions"] if item["id"] == "codex-agents-install"
            )
            self.assertEqual(template_action["mode"], "plan-only")

    def test_config_template_is_materialized_after_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex"
            codex_home.mkdir()
            seed = bootstrap.codex_static.template("config.toml.seed").replace(
                "{{PENNIX_BASE_URL}}", "https://api.example.test/v1"
            )
            config = codex_home / "config.toml"
            config.write_text(seed, encoding="utf-8")
            planned = self.run_cli(root, "plan")
            self.assertEqual(planned.returncode, 0, planned.stderr)
            config_action = next(
                item for item in json.loads(planned.stdout)["actions"] if item["id"] == "codex-config-install"
            )
            self.assertEqual(config_action["status"], "seeded")
            self.assertEqual(config_action["mode"], "applyable")
            applied = self.run_cli(
                root,
                "--state-dir",
                str(root / "state"),
                "apply",
                "--action",
                "codex-config-install",
                "--yes",
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            current = config.read_text(encoding="utf-8")
            self.assertEqual(bootstrap.codex_static.config_state(current), "current")
            tomllib.loads(current)

            receipt = Path(json.loads(applied.stdout)["receipt"])
            rolled_back = self.run_cli(
                root,
                "--state-dir",
                str(root / "state"),
                "rollback",
                "--receipt",
                str(receipt),
            )
            self.assertEqual(rolled_back.returncode, 0, rolled_back.stderr)
            self.assertEqual(config.read_text(encoding="utf-8"), seed)

    def test_unsupported_host_blocks_all_write_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = bootstrap.load_catalog(self.catalog(root))
            inventory = {
                "static": {
                    "agents_path": str(root / "AGENTS.md"),
                    "agents_template": "absent",
                    "config_path": str(root / "config.toml"),
                    "config_install": "absent",
                },
                "source": {"path": str(SOURCE_ROOT), "ready": True},
                "host": {"supported": False, "reason": "Arch Linux only"},
                "components": {},
            }
            planned = bootstrap.plan(argparse.Namespace(project_root=root), inventory, catalog)
            self.assertTrue(all(item["mode"] == "blocked" for item in planned["actions"]))

    def test_package_owner_parser(self) -> None:
        self.assertEqual(
            bootstrap.parse_package_owner("/usr/bin/codex is owned by openai-codex-bin 0.154.0-1"),
            "openai-codex-bin",
        )
        self.assertIsNone(bootstrap.parse_package_owner("No package owns this file"))


if __name__ == "__main__":
    unittest.main()
