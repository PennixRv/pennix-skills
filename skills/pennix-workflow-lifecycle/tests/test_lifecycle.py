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
SCRIPT = SKILL_ROOT / "scripts" / "lifecycle.py"
sys.path.insert(0, str(SCRIPT.parent))

import lifecycle as bootstrap


class BootstrapTests(unittest.TestCase):
    def catalog(self, root: Path) -> Path:
        catalog = root / "catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "schema": 2,
                    "components": {
                        "fixture": {
                            "delivery": "package",
                            "approved_version": "1.2.3",
                            "source": "fixture",
                            "owner": "test",
                            "scope": "global",
                            "verify_key": "fixture --version",
                            "probe": "fixture",
                            "version_args": ["--version"],
                            "actions": {name: "managed" for name in ("install", "configure", "upgrade", "uninstall", "verify")},
                            "project_init": "not-applicable",
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
                *arguments,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_discover_and_verify_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            discover = self.run_cli(root, "discover")
            self.assertEqual(discover.returncode, 0, discover.stderr)
            self.assertIn("components", json.loads(discover.stdout))

            verify = self.run_cli(root, "verify")
            self.assertEqual(verify.returncode, 2, verify.stderr)
            self.assertEqual(json.loads(verify.stdout)["verification"]["status"], "blocked")
            self.assertIn("observed status is missing", verify.stderr)
            self.assertIn("components", json.loads(verify.stdout))
            self.assertFalse((root / "codex").exists())

    def test_discover_reports_catalog_candidate_and_actual_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = bootstrap.load_catalog(self.catalog(root))
            args = SimpleNamespace(
                catalog=self.catalog(root),
                codex_home=root / "codex",
                destination=None,
            )
            with (
                patch.object(bootstrap, "probe_component", return_value=("drifted", "1.0.0")),
                patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
                patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
                patch.object(bootstrap.host, "detect_host", return_value={"installers": {"official": "pacman"}}),
                patch.object(bootstrap, "package_candidate_version", return_value="1.2.3"),
            ):
                inventory = bootstrap.discover(args, catalog)
            fixture = inventory["components"]["fixture"]
            self.assertEqual(fixture["catalog_version"], "1.2.3")
            self.assertEqual(fixture["candidate_version"], "1.2.3")
            self.assertEqual(fixture["observed_package"], "fixture-package")
            self.assertEqual(fixture["target_package"], "fixture-package")

    def test_repository_latest_catalog_is_aur_only_and_has_no_pinned_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = self.catalog(root)
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            component = value["components"]["fixture"]
            component.pop("approved_version")
            component["version_policy"] = "repository-latest"
            component["package"]["source"] = "aur"
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(
                bootstrap.load_catalog(catalog_path)["components"]["fixture"]["version_policy"],
                "repository-latest",
            )

            component["approved_version"] = "1.2.3"
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(bootstrap.BootstrapError, "repository-latest"):
                bootstrap.load_catalog(catalog_path)

    def test_repository_latest_probe_matches_the_current_aur_candidate(self) -> None:
        component = {
            "version_policy": "repository-latest",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "aur", "name": "fixture-package"},
        }
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"installers": {"aur": "yay"}}),
            patch.object(bootstrap, "package_candidate_version", return_value="1.2.3"),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(
                bootstrap.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="fixture 1.2.3", stderr=""),
            ),
            patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
        ):
            self.assertEqual(bootstrap.probe_component(component), ("match", "1.2.3"))

    def test_discover_reports_repository_latest_policy_and_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = self.catalog(root)
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            component = value["components"]["fixture"]
            component.pop("approved_version")
            component["version_policy"] = "repository-latest"
            component["package"]["source"] = "aur"
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            catalog = bootstrap.load_catalog(catalog_path)
            args = SimpleNamespace(catalog=catalog_path, codex_home=root / "codex", destination=None)
            with (
                patch.object(bootstrap, "probe_component", return_value=("drifted", "1.0.0")),
                patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
                patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
                patch.object(bootstrap.host, "detect_host", return_value={"installers": {"aur": "yay"}}),
                patch.object(bootstrap, "package_candidate_version", return_value="1.2.3"),
            ):
                discovered = bootstrap.discover(args, catalog)["components"]["fixture"]
            self.assertIsNone(discovered["catalog_version"])
            self.assertEqual(discovered["version_policy"], "repository-latest")
            self.assertEqual(discovered["candidate_version"], "1.2.3")

    def test_verify_reports_match_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = bootstrap.load_catalog(self.catalog(root))
            inventory = {
                "components": {
                    "fixture": {"status": "match"},
                }
            }
            args = SimpleNamespace()
            self.assertEqual(bootstrap.verify_inventory(args, catalog, inventory), [])
            self.assertEqual(inventory["verification"]["status"], "match")

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

    def test_final_version_is_used_after_an_update_notice(self) -> None:
        self.assertEqual(
            bootstrap.normalize_version("update available: 0.6.39 -> 0.6.41\n0.6.41"),
            "0.6.41",
        )

    def test_normalize_version_preserves_semver_prerelease(self) -> None:
        self.assertEqual(bootstrap.normalize_version("trellis 0.7.0-beta.8"), "0.7.0-beta.8")

    def test_configure_is_a_supported_command(self) -> None:
        self.assertEqual(bootstrap.parse_args(["configure"]).command, "configure")

    def test_static_install_upgrade_and_uninstall_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "codex"
            home.mkdir()
            config = home / "config.toml"
            config.write_text(bootstrap.codex_static.seed_config("https://api.example.test/v1"), encoding="utf-8")
            args = SimpleNamespace(codex_home=home, destination=None)

            config_component = {"adapter": "codex-config"}
            agents_component = {"adapter": "codex-agents"}
            self.assertEqual(bootstrap.static_operation(args, "codex-config", config_component, "install"), "changed")
            self.assertEqual(bootstrap.static_operation(args, "codex-config", config_component, "configure"), "no-op")
            self.assertEqual(bootstrap.static_operation(args, "codex-config", config_component, "upgrade"), "no-op")
            self.assertEqual(bootstrap.static_operation(args, "codex-config", config_component, "uninstall"), "changed")
            self.assertEqual(bootstrap.codex_static.config_state(config.read_text(encoding="utf-8")), "seeded")

            self.assertEqual(bootstrap.static_operation(args, "codex-agents", agents_component, "install"), "changed")
            self.assertEqual(bootstrap.static_operation(args, "codex-agents", agents_component, "uninstall"), "changed")
            self.assertEqual(bootstrap.static_operation(args, "codex-agents", agents_component, "uninstall"), "no-op")

    def test_static_uninstall_refuses_drifted_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            target = home / "AGENTS.md"
            target.write_text("# user instructions\n", encoding="utf-8")
            args = SimpleNamespace(codex_home=home, destination=None)
            with self.assertRaisesRegex(bootstrap.BootstrapError, "refusing drifted"):
                bootstrap.static_operation(args, "codex-agents", {"adapter": "codex-agents"}, "uninstall")
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
        self.assertEqual(run.call_args.args[0], ["sudo", "pacman", "-S", "--needed", "--noconfirm", "fixture-package"])

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
        self.assertEqual(run.call_args.args[0], ["sudo", "pacman", "-R", "--noconfirm", "fixture-package"])

    def test_repository_latest_upgrade_uses_the_current_aur_candidate(self) -> None:
        component = {
            "version_policy": "repository-latest",
            "source": "fixture",
            "owner": "test",
            "scope": "global",
            "verify_key": "fixture --version",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "aur", "name": "fixture-package"},
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"))
        host_state = {"supported": True, "installers": {"aur": "yay"}}
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
        self.assertEqual(run.call_args.args[0], ["yay", "-S", "--needed", "--noconfirm", "fixture-package"])

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

    def test_collection_discover_and_verify_need_no_source_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            catalog_path = self.catalog(root)
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            value["components"] = {
                "pennix-skills": {
                    "delivery": "collection",
                    "source": "public GitHub Skills installed by Codex system $skill-installer",
                    "owner": "pennix",
                    "scope": "global",
                    "verify_key": "skills/pennix-skills direct entry set",
                    "actions": {
                        "install": "native-owner",
                        "configure": "not-applicable",
                        "upgrade": "native-owner",
                        "uninstall": "managed",
                        "verify": "managed",
                    },
                    "project_init": "not-applicable",
                    "adapter": "pennix-skills",
                    "native_owner_reason": "Codex system $skill-installer owns installation.",
                    "collection_contract": {
                        "skills": ["alpha", "beta"],
                        "bootstrap_skill": "alpha",
                        "source": {"repo": "PennixRv/fixture", "ref": "main", "paths": ["skills/alpha", "skills/beta"]},
                        "materialized": {},
                    },
                }
            }
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            for name in ("alpha", "beta"):
                skill = destination / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Fixture.\n---\n",
                    encoding="utf-8",
                )

            args = SimpleNamespace(catalog=catalog_path, codex_home=root / "codex", destination=str(destination))
            catalog = bootstrap.load_catalog(catalog_path)
            inventory = bootstrap.discover(args, catalog)

            self.assertEqual(inventory["components"]["pennix-skills"]["status"], "match")
            self.assertNotIn("source", inventory)
            self.assertEqual(bootstrap.verify_inventory(args, catalog, inventory), [])

    def test_collection_discover_reports_missing_names_for_a_safe_partial_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            catalog_path = self.catalog(root)
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            value["components"] = {
                "pennix-skills": {
                    "delivery": "collection",
                    "source": "fixture",
                    "owner": "pennix",
                    "scope": "global",
                    "verify_key": "fixture",
                    "actions": {"install": "native-owner", "configure": "not-applicable", "upgrade": "native-owner", "uninstall": "managed", "verify": "managed"},
                    "project_init": "not-applicable",
                    "adapter": "pennix-skills",
                    "native_owner_reason": "fixture",
                    "collection_contract": {
                        "skills": ["alpha", "beta", "bootstrap"],
                        "bootstrap_skill": "bootstrap",
                        "source": {"repo": "PennixRv/fixture", "ref": "main", "paths": ["skills/alpha", "skills/beta", "skills/bootstrap"]},
                        "materialized": {},
                    },
                }
            }
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            for name in ("alpha", "bootstrap"):
                skill = destination / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Fixture.\n---\n",
                    encoding="utf-8",
                )

            args = SimpleNamespace(catalog=catalog_path, codex_home=root / "codex", destination=str(destination))
            inventory = bootstrap.discover(args, bootstrap.load_catalog(catalog_path))

            self.assertEqual(inventory["components"]["pennix-skills"]["status"], "partial")
            self.assertEqual(inventory["components"]["pennix-skills"]["missing_skills"], ["beta"])

    def test_collection_install_and_upgrade_are_owned_by_system_installer(self) -> None:
        args = SimpleNamespace(command="install", component="pennix-skills", yes=True)
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        with self.assertRaisesRegex(bootstrap.BootstrapError, "native-owner"):
            bootstrap.run_lifecycle(args, catalog)

    def test_replace_staged_collection_uses_catalog_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            staging = root / "skills" / ".pennix-skills-stage"
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            component = catalog["components"]["pennix-skills"]
            for name in bootstrap.collection_skill_names(component):
                skill = staging / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Fixture.\n---\n",
                    encoding="utf-8",
                )
            args = SimpleNamespace(
                component="pennix-skills",
                yes=True,
                staging=str(staging),
                destination=str(destination),
            )

            bootstrap.replace_staged_collection(args, catalog)

            self.assertEqual(bootstrap.probe_component(component, root / "codex", str(destination))[0], "match")

        args.command = "upgrade"
        with self.assertRaisesRegex(bootstrap.BootstrapError, "native-owner"):
            bootstrap.run_lifecycle(args, catalog)

    def test_collection_uninstall_removes_an_exact_installed_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            component = catalog["components"]["pennix-skills"]
            for name in bootstrap.collection_skill_names(component):
                skill = destination / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Fixture.\n---\n",
                    encoding="utf-8",
                )
            args = SimpleNamespace(codex_home=root / "codex", destination=str(destination))

            self.assertEqual(bootstrap.static_operation(args, "pennix-skills", component, "uninstall"), "changed")
            self.assertFalse(destination.exists())

    def test_collection_bootstrap_state_is_known_and_removable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            component = catalog["components"]["pennix-skills"]
            name = bootstrap.collection_bootstrap_skill(component)
            skill = destination / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Fixture.\n---\n",
                encoding="utf-8",
            )
            args = SimpleNamespace(codex_home=root / "codex", destination=str(destination))

            self.assertEqual(bootstrap.probe_component(component, args.codex_home, args.destination)[0], "bootstrap")
            self.assertEqual(bootstrap.static_operation(args, "pennix-skills", component, "uninstall"), "changed")
            self.assertFalse(destination.exists())

    def test_collection_contract_names_every_current_skill(self) -> None:
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        component = catalog["components"]["pennix-skills"]
        expected = bootstrap.collection_skill_names(component)
        observed = {
            directory.name
            for directory in SKILL_ROOT.parent.iterdir()
            if directory.is_dir() and (directory / "SKILL.md").is_file()
        }
        self.assertEqual(expected, observed)
        contract = component["collection_contract"]
        self.assertEqual(bootstrap.collection_source_names(contract["source"]) | bootstrap.collection_materialized_names(contract["materialized"]), expected)

    def test_materialized_snapshots_exclude_repository_runtime_metadata(self) -> None:
        forbidden = {".agents", ".codex", ".github", ".trellis", "dist", "node_modules", "__pycache__"}
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        contract = catalog["components"]["pennix-skills"]["collection_contract"]
        for name in contract["materialized"]:
            entries = {entry.name for entry in (SKILL_ROOT.parent / name).iterdir()}
            self.assertFalse(entries & forbidden, name)

    def test_default_catalog_accepts_scoped_npm_packages(self) -> None:
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        self.assertEqual(catalog["components"]["fastctx"]["package"]["name"], "@pennixrv/fastctx")
        self.assertEqual(catalog["components"]["fastctx"]["replaces"], ["fastctx"])
        self.assertEqual(catalog["components"]["codex-cli"]["package"]["source"], "aur")
        self.assertEqual(catalog["components"]["codex-cli"]["version_policy"], "repository-latest")
        self.assertNotIn("approved_version", catalog["components"]["codex-cli"])
        self.assertEqual(catalog["components"]["ponytail-plugin"]["plugin"]["id"], "ponytail@ponytail")
        self.assertEqual(catalog["components"]["trellis-cli"]["approved_version"], "0.7.0-beta.8")

    def test_npm_replacement_is_removed_before_install(self) -> None:
        component = {
            "approved_version": "2.0.0",
            "probe": "fastctx",
            "version_args": ["--version"],
            "package": {"source": "npm", "name": "@example/fastctx", "registry": "https://registry.npmjs.org/"},
            "replaces": ["fastctx"],
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"), destination=None)
        host_state = {"supported": True, "installers": {"npm": "npm"}}
        with (
            patch.object(bootstrap.host, "detect_host", return_value=host_state),
            patch.object(bootstrap, "probe_component", side_effect=[("drifted", "1.0.0"), ("match", "2.0.0")]),
            patch.object(bootstrap, "installed_npm_packages", side_effect=[{"fastctx": "1.0.0"}, {}, {}]),
            patch.object(bootstrap, "npm_global_root", return_value=None),
            patch.object(bootstrap, "npm_owner_for_command", return_value="fastctx"),
            patch.object(bootstrap, "package_candidate_version", return_value="2.0.0"),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fastctx"),
            patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run,
        ):
            self.assertEqual(
                bootstrap.component_operation(args, {"components": {}}, "fastctx", component, "upgrade"),
                "changed",
            )
        self.assertEqual(run.call_args_list[0].args[0], ["npm", "uninstall", "--global", "fastctx"])
        self.assertEqual(run.call_args_list[1].args[0][-1], "@example/fastctx@2.0.0")

    def test_match_cleans_catalogued_npm_replacement(self) -> None:
        component = {
            "approved_version": "2.0.0",
            "probe": "fastctx",
            "version_args": ["--version"],
            "package": {"source": "npm", "name": "@example/fastctx", "registry": "https://registry.npmjs.org/"},
            "replaces": ["fastctx"],
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"), destination=None)
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"supported": True, "installers": {"npm": "npm"}}),
            patch.object(bootstrap, "probe_component", return_value=("match", "2.0.0")),
            patch.object(bootstrap, "installed_npm_packages", side_effect=[{"fastctx": "1.0.0"}, {}]),
            patch.object(bootstrap, "npm_global_root", return_value=None),
            patch.object(bootstrap, "npm_owner_for_command", return_value="@example/fastctx"),
            patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run,
        ):
            self.assertEqual(bootstrap.component_operation(args, {"components": {}}, "fastctx", component, "upgrade"), "changed")
        run.assert_called_once_with(["npm", "uninstall", "--global", "fastctx"], check=False)

    def test_match_cleans_catalogued_package_replacement(self) -> None:
        component = {
            "approved_version": "2.0.0",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "aur", "name": "fixture-package"},
            "replaces": ["legacy-package"],
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"), destination=None)
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"supported": True, "installers": {"aur": "yay"}}),
            patch.object(bootstrap, "probe_component", return_value=("match", "2.0.0")),
            patch.object(bootstrap, "installed_pacman_package", side_effect=[True, False]),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
            patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run,
        ):
            self.assertEqual(
                bootstrap.component_operation(args, {"components": {}}, "fixture", component, "upgrade"), "changed"
            )
        run.assert_called_once_with(["yay", "-R", "--noconfirm", "legacy-package"], check=False)

    def test_system_npm_root_uses_sudo_for_package_actions(self) -> None:
        component = {"package": {"source": "npm"}}
        with (
            patch.object(bootstrap, "npm_global_root", return_value=Path("/usr/lib/node_modules")),
            patch.object(bootstrap.os, "access", return_value=False),
        ):
            self.assertEqual(
                bootstrap.package_command(component, ["npm", "install", "--global", "pkg"]),
                ["sudo", "npm", "install", "--global", "pkg"],
            )
            self.assertEqual(
                bootstrap.package_command({"source": "npm"}, ["npm", "uninstall", "--global", "pkg"]),
                ["sudo", "npm", "uninstall", "--global", "pkg"],
            )

    def test_unmanaged_package_owner_is_blocked(self) -> None:
        component = {
            "approved_version": "1.2.3",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "official", "name": "fixture-package"},
        }
        args = SimpleNamespace(codex_home=Path("/tmp/codex"), destination=None)
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"supported": True, "installers": {"official": "pacman"}}),
            patch.object(bootstrap, "probe_component", return_value=("drifted", "1.0.0")),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(bootstrap, "installed_package_owner", return_value="unrelated-package"),
            self.assertRaisesRegex(bootstrap.BootstrapError, "unmanaged package"),
        ):
            bootstrap.component_operation(args, {"components": {}}, "fixture", component, "upgrade")

    def test_catalog_contains_static_components_and_capabilities(self) -> None:
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        self.assertEqual(catalog["schema"], 2)
        self.assertEqual(catalog["components"]["codex-config"]["delivery"], "static")
        self.assertEqual(catalog["components"]["cch-status"]["actions"]["install"], "native-owner")
        self.assertEqual(catalog["components"]["pennix-skills"]["delivery"], "collection")

    def test_non_managed_action_is_rejected_before_adapter(self) -> None:
        args = SimpleNamespace(command="install", component="cch-status", yes=True)
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        with self.assertRaisesRegex(bootstrap.BootstrapError, "native-owner"):
            bootstrap.run_lifecycle(args, catalog)


if __name__ == "__main__":
    unittest.main()
