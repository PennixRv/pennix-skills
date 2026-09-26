from __future__ import annotations

import json
import os
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
    def setUp(self) -> None:
        self._state_directory = tempfile.TemporaryDirectory()
        self._state_environment = patch.dict(os.environ, {"XDG_STATE_HOME": self._state_directory.name})
        self._state_environment.start()

    def tearDown(self) -> None:
        self._state_environment.stop()
        self._state_directory.cleanup()

    def trust_collection(self, destination: Path) -> None:
        staged = bootstrap.skills_install._write_receipt(destination, bootstrap.skills_install.collection_digest(destination))
        os.replace(staged, bootstrap.skills_install.receipt_path(destination))

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
                            "actions": {name: "managed" for name in ("install", "configure", "upgrade", "uninstall", "verify", "reconcile")},
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

    def test_staging_is_an_unknown_advisory_and_does_not_block_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            destination.mkdir(parents=True)
            (destination.parent / ".pennix-skills-stage-example").mkdir()
            catalog_path = self.catalog(root)
            catalog = bootstrap.load_catalog(catalog_path)
            args = SimpleNamespace(
                catalog=catalog_path,
                codex_home=root / "codex",
                destination=str(destination),
            )
            with (
                patch.object(bootstrap, "probe_component", return_value=("match", "1.2.3")),
                patch.object(bootstrap.host, "detect_host", return_value={"supported": True, "installers": {}}),
                patch.object(bootstrap.shutil, "which", return_value=None),
            ):
                inventory = bootstrap.discover(args, catalog)
                failures = bootstrap.verify_inventory(args, catalog, inventory)
            self.assertEqual(failures, [])
            self.assertEqual(inventory["staging"], {"status": "unknown", "candidates": [".pennix-skills-stage-example"]})
            self.assertIn("staging state is unknown", inventory["verification"]["advisories"][0])

    def test_reconcile_migrates_exact_legacy_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "codex"
            legacy = home / "pennix-workflow-lifecycle"
            static = legacy / "static-assets"
            static.mkdir(parents=True)
            os.chmod(static, 0o700)
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            profile = legacy / "profile.json"
            profile.write_text(
                json.dumps({"schema": 1, "catalog_digest": bootstrap.configuration_digest(catalog), "targets": []}) + "\n",
                encoding="utf-8",
            )
            receipt = static / "tmux-config.json"
            receipt.write_text(
                json.dumps(bootstrap.tmux_static._receipt_value("sha256:" + "a" * 64, "sha256:" + "b" * 64)) + "\n",
                encoding="utf-8",
            )
            os.chmod(profile, 0o600)
            os.chmod(receipt, 0o600)
            args = SimpleNamespace(component=bootstrap.STATE_COMPONENT, yes=True, codex_home=home)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "state")}):
                result = bootstrap.reconcile_state(args, catalog)
                self.assertEqual(result["status"], "migrated")
                self.assertTrue(bootstrap.configuration.profile_path(home).is_file())
                self.assertTrue(bootstrap.tmux_static.receipt_path(home).is_file())
            self.assertFalse(legacy.exists())

    def test_reconcile_keeps_legacy_on_destination_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "codex"
            legacy = home / "pennix-workflow-lifecycle"
            legacy.mkdir(parents=True)
            profile = legacy / "profile.json"
            original = json.dumps({"schema": 1, "catalog_digest": "a" * 64, "targets": []}) + "\n"
            profile.write_text(original, encoding="utf-8")
            os.chmod(profile, 0o600)
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "state")}):
                destination = bootstrap.configuration.profile_path(home)
                bootstrap.configuration.ensure_state_namespace(bootstrap.configuration.state_namespace(home))
                destination.write_text(json.dumps({"schema": 1, "catalog_digest": "c" * 64, "targets": []}) + "\n", encoding="utf-8")
                os.chmod(destination, 0o600)
                result = bootstrap.reconcile_state(
                    SimpleNamespace(component=bootstrap.STATE_COMPONENT, yes=True, codex_home=home), catalog
                )
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(profile.is_file())
            self.assertEqual(profile.read_text(encoding="utf-8"), original)

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

    def test_repository_latest_probe_reports_an_upgrade_without_blocking_state(self) -> None:
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
                return_value=SimpleNamespace(returncode=0, stdout="fixture 1.0.0", stderr=""),
            ),
            patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
        ):
            self.assertEqual(bootstrap.probe_component(component), ("upgrade-available", "1.0.0"))

    def test_repository_latest_aur_probe_ignores_the_package_release_suffix(self) -> None:
        component = {
            "version_policy": "repository-latest",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "aur", "name": "fixture-package"},
        }
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"installers": {"aur": "yay"}}),
            patch.object(bootstrap, "package_candidate_version", return_value="1.2.3-1"),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(
                bootstrap.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="fixture 1.2.3", stderr=""),
            ),
            patch.object(bootstrap, "installed_package_owner", return_value="fixture-package"),
        ):
            self.assertEqual(bootstrap.probe_component(component), ("match", "1.2.3"))

    def test_repository_latest_probe_blocks_when_candidate_is_unavailable(self) -> None:
        component = {
            "version_policy": "repository-latest",
            "probe": "fixture",
            "version_args": ["--version"],
            "package": {"source": "aur", "name": "fixture-package"},
        }
        with (
            patch.object(bootstrap.host, "detect_host", return_value={"installers": {"aur": "yay"}}),
            patch.object(bootstrap, "package_candidate_version", return_value=None),
            patch.object(bootstrap.shutil, "which", return_value="/usr/bin/fixture"),
            patch.object(
                bootstrap.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="fixture 1.0.0", stderr=""),
            ),
        ):
            self.assertEqual(bootstrap.probe_component(component), ("unknown", "1.0.0"))

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
            self.assertEqual(inventory["verification"]["scope"], "full")
            self.assertEqual(inventory["verification"]["checked_components"], ["fixture"])
            self.assertEqual(inventory["verification"]["advisories"], [])

    def test_component_verify_isolated_from_unrelated_components(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = self.catalog(root)
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            value["components"]["other"] = dict(value["components"]["fixture"])
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            catalog = bootstrap.load_catalog(catalog_path)
            inventory = {"components": {"fixture": {"status": "match"}, "other": {"status": "missing"}}}

            args = SimpleNamespace(component="fixture")
            self.assertEqual(bootstrap.verify_inventory(args, catalog, inventory), [])
            self.assertEqual(inventory["verification"]["scope"], "component")
            self.assertEqual(inventory["verification"]["checked_components"], ["fixture"])

            full_args = SimpleNamespace()
            self.assertEqual(bootstrap.verify_inventory(full_args, catalog, inventory), ["other: observed status is missing"])

    def test_component_verify_reports_upgrade_as_advisory(self) -> None:
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
            inventory = {"components": {"fixture": {"status": "upgrade-available"}}}

            args = SimpleNamespace(component="fixture")
            self.assertEqual(bootstrap.verify_inventory(args, catalog, inventory), [])
            self.assertEqual(inventory["verification"]["status"], "match")
            self.assertEqual(inventory["verification"]["advisories"], ["fixture: upgrade available"])

    def test_full_verify_keeps_configuration_and_pinned_drift_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = self.catalog(root)
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            value["configuration_targets"] = [
                {
                    "id": "fixture-provider",
                    "tier": "core",
                    "default_enabled": True,
                    "adapter": "codex-provider",
                    "component": "fixture",
                    "readiness": "fixture",
                }
            ]
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            catalog = bootstrap.load_catalog(catalog_path)
            inventory = {
                "components": {"fixture": {"status": "drifted"}},
                "configuration": {
                    "targets": [{"id": "fixture-provider", "tier": "core", "enabled": True, "status": "blocked"}],
                    "profile_status": "stale",
                },
            }

            args = SimpleNamespace(component="fixture")
            self.assertEqual(bootstrap.verify_inventory(args, catalog, inventory), ["fixture: observed status is drifted"])
            self.assertEqual(inventory["verification"]["scope"], "component")

            full = SimpleNamespace()
            failures = bootstrap.verify_inventory(full, catalog, inventory)
            self.assertEqual(
                failures,
                [
                    "fixture: observed status is drifted",
                    "configuration fixture-provider: status is blocked",
                    "configuration profile is stale",
                ],
            )

    def test_component_verify_rejects_unknown_selector(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = bootstrap.load_catalog(self.catalog(root))
            with self.assertRaisesRegex(bootstrap.BootstrapError, "unknown lifecycle component"):
                bootstrap.verify_inventory(SimpleNamespace(component="missing"), catalog, {"components": {}})

            result = self.run_cli(root, "verify", "--component", "missing")
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown lifecycle component", result.stderr)

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

    def test_configuration_contract_rejects_unknown_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog_path = self.catalog(Path(temporary))
            value = json.loads(catalog_path.read_text(encoding="utf-8"))
            value["configuration_targets"] = [
                {
                    "id": "fixture-credential",
                    "tier": "optional",
                    "default_enabled": False,
                    "adapter": "grok-provider",
                    "component": "missing-component",
                    "readiness": "fixture",
                }
            ]
            catalog_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(bootstrap.BootstrapError, "configuration target component"):
                bootstrap.load_catalog(catalog_path)

    def test_configuration_target_persists_only_its_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog_path = self.catalog(root)
            catalog = bootstrap.load_catalog(catalog_path)
            catalog["configuration_targets"] = [
                {
                    "id": "fixture-provider",
                    "tier": "core",
                    "default_enabled": True,
                    "adapter": "codex-provider",
                    "component": "fixture",
                    "readiness": "fixture",
                }
            ]
            args = SimpleNamespace(
                command="configure",
                component="fixture-provider",
                yes=True,
                catalog=catalog_path,
                codex_home=root / "codex",
                destination=None,
            )
            with (
                patch.object(bootstrap, "configuration_parent_status"),
                patch.object(bootstrap.configuration, "configure_target", return_value="ready"),
            ):
                bootstrap.run_lifecycle(args, catalog)
            profile_state, selected = bootstrap.configuration.load_profile(
                args.codex_home,
                bootstrap.configuration_digest(catalog),
            )
            self.assertEqual(profile_state, "match")
            self.assertEqual(selected, {"fixture-provider"})

    def test_codex_config_requires_private_native_auth_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = home / "config.toml"
            config.write_text(bootstrap.codex_static.seed_config("https://example.test"), encoding="utf-8")
            self.assertEqual(bootstrap.probe_component({"adapter": "codex-config"}, home)[0], "drifted")
            auth = home / "auth.json"
            auth.write_text('{"access_token":"redacted"}\n', encoding="utf-8")
            os.chmod(auth, 0o600)
            self.assertEqual(bootstrap.probe_component({"adapter": "codex-config"}, home)[0], "match")

    def test_codex_config_accepts_compatible_user_extensions_without_rewriting_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = home / "config.toml"
            config.write_text(
                bootstrap.codex_static.install_config("https://example.test")
                + "\n[projects.\"/home/example\"]\ntrust_level = \"trusted\"\n",
                encoding="utf-8",
            )
            self.assertEqual(bootstrap.codex_static.config_state(config.read_text(encoding="utf-8")), "compatible")

            legacy = config.read_text(encoding="utf-8").replace(
                "# Pennix Codex seed configuration. Only seed-owned fields appear here.\n"
                "# pennix-workflow-lifecycle:seed-config\n",
                "# Existing user configuration.\n",
            )
            config.write_text(legacy, encoding="utf-8")
            self.assertEqual(bootstrap.codex_static.config_state(legacy), "compatible")
            args = SimpleNamespace(codex_home=home, destination=None)
            before = config.read_text(encoding="utf-8")
            self.assertEqual(
                bootstrap.static_operation(args, "codex-config", {"adapter": "codex-config"}, "upgrade"),
                "no-op",
            )
            self.assertEqual(config.read_text(encoding="utf-8"), before)

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
            self.assertEqual(
                bootstrap.static_operation(args, "codex-agents", {"adapter": "codex-agents"}, "uninstall"),
                "no-op",
            )
            self.assertTrue(target.exists())

    def test_agents_install_adds_missing_owned_blocks_without_replacing_custom_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            target = home / "AGENTS.md"
            template = bootstrap.codex_static.template("AGENTS.md.install")
            fastctx = bootstrap.codex_static._agent_block(
                template,
                "<!-- pennix-fastctx:begin -->",
                "<!-- pennix-fastctx:end -->",
            )
            self.assertIsNotNone(fastctx)
            original = "# user instructions\n\n" + fastctx + "\n"
            target.write_text(original, encoding="utf-8")
            args = SimpleNamespace(codex_home=home, destination=None)

            self.assertEqual(
                bootstrap.static_operation(args, "codex-agents", {"adapter": "codex-agents"}, "install"),
                "changed",
            )
            updated = target.read_text(encoding="utf-8")
            self.assertIn("# user instructions", updated)
            self.assertIn("$pennix-fastctx", updated)
            self.assertEqual(updated.count("<!-- pennix-workflow-lifecycle:begin -->"), 1)

    def test_agents_install_refuses_modified_owned_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            target = home / "AGENTS.md"
            target.write_text(
                "<!-- pennix-fastctx:begin -->\nmodified\n<!-- pennix-fastctx:end -->\n",
                encoding="utf-8",
            )
            args = SimpleNamespace(codex_home=home, destination=None)
            with self.assertRaisesRegex(bootstrap.codex_static.StaticError, "pennix-fastctx"):
                bootstrap.static_operation(args, "codex-agents", {"adapter": "codex-agents"}, "install")

    def test_agents_install_refuses_duplicate_owned_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            target = home / "AGENTS.md"
            block = "<!-- pennix-fastctx:begin -->\nkeep\n<!-- pennix-fastctx:end -->\n"
            target.write_text(block + block, encoding="utf-8")
            args = SimpleNamespace(codex_home=home, destination=None)
            with self.assertRaisesRegex(bootstrap.codex_static.StaticError, "markers are invalid"):
                bootstrap.static_operation(args, "codex-agents", {"adapter": "codex-agents"}, "install")

    def tmux_fixture(self, root: Path) -> tuple[SimpleNamespace, dict[str, object], Path, Path]:
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        component = catalog["components"]["tmux-config"]
        codex_home = root / "codex"
        home = root / "home"
        codex_home.mkdir()
        home.mkdir()
        return SimpleNamespace(codex_home=codex_home, home_directory=home, destination=None), component, codex_home, home

    def test_tmux_static_preserves_existing_cch_content_and_reenters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args, component, codex_home, home = self.tmux_fixture(root)
            target = home / ".tmux.conf"
            original = (
                'set -g @user-option "keep-me"\n'
                "# >>> cch-codex-tmux-status managed block >>>\n"
                "set-option -g focus-events on\n"
                "# <<< cch-codex-tmux-status managed block <<<\n"
            )
            target.write_bytes(original.encode())
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                self.assertEqual(bootstrap.static_operation(args, "tmux-config", component, "install"), "changed")
                first = target.read_bytes()
                self.assertIn(original.encode(), first)
                self.assertEqual(bootstrap.static_operation(args, "tmux-config", component, "configure"), "no-op")
                self.assertEqual(bootstrap.static_operation(args, "tmux-config", component, "verify"), "no-op")
            receipt = bootstrap.tmux_static.receipt_path(codex_home)
            self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
            self.assertEqual(target.read_bytes(), first)
            self.assertEqual(bootstrap.tmux_static.inspect(codex_home, home, component["template"]["revision"])["state"], "current")
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                self.assertEqual(bootstrap.static_operation(args, "tmux-config", component, "uninstall"), "changed")
            self.assertEqual(target.read_bytes(), original.encode())
            self.assertFalse(receipt.exists())

    def test_tmux_static_upgrades_only_an_owned_old_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args, component, codex_home, home = self.tmux_fixture(root)
            old_revision = "sha256:" + "0" * 64
            old_body = "set -g default-terminal \"xterm-256color\""
            old_block, old_digest = bootstrap.tmux_static._block(old_revision, old_body)
            target = home / ".tmux.conf"
            prefix = b"# user prefix\r\n"
            suffix = b"\r\n# user suffix\r\n"
            target.write_bytes(prefix + old_block.encode() + suffix)
            bootstrap.tmux_static._write_receipt(
                bootstrap.tmux_static.receipt_path(codex_home),
                bootstrap.tmux_static._receipt_value(old_revision, old_digest),
            )
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                self.assertEqual(
                    bootstrap.static_operation(args, "tmux-config", component, "upgrade"),
                    "changed",
                )
            contents = target.read_bytes()
            self.assertTrue(contents.startswith(prefix))
            self.assertTrue(contents.endswith(suffix))
            self.assertEqual(
                bootstrap.tmux_static.inspect(codex_home, home, component["template"]["revision"])["state"],
                "current",
            )

    def test_tmux_static_refuses_drift_and_missing_dependency_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args, component, _, home = self.tmux_fixture(root)
            target = home / ".tmux.conf"
            target.write_text("# user file\n", encoding="utf-8")
            before = target.read_bytes()
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value=None):
                with self.assertRaisesRegex(bootstrap.BootstrapError, "dependency"):
                    bootstrap.static_operation(args, "tmux-config", component, "install")
            self.assertEqual(target.read_bytes(), before)

            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                bootstrap.static_operation(args, "tmux-config", component, "install")
                target.write_text(target.read_text(encoding="utf-8").replace("# block-digest:", "# block-digest: sha256:"), encoding="utf-8")
                drifted = target.read_bytes()
                with self.assertRaisesRegex(bootstrap.BootstrapError, "refusing drifted"):
                    bootstrap.static_operation(args, "tmux-config", component, "upgrade")
            self.assertEqual(target.read_bytes(), drifted)

    def test_tmux_static_refuses_missing_receipt_duplicate_markers_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args, component, codex_home, home = self.tmux_fixture(root)
            target = home / ".tmux.conf"
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                bootstrap.static_operation(args, "tmux-config", component, "install")
            receipt = bootstrap.tmux_static.receipt_path(codex_home)
            receipt.unlink()
            before = target.read_bytes()
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                with self.assertRaisesRegex(bootstrap.BootstrapError, "receipt"):
                    bootstrap.static_operation(args, "tmux-config", component, "upgrade")
            self.assertEqual(target.read_bytes(), before)

            receipt.parent.mkdir(parents=True, exist_ok=True)
            bootstrap.tmux_static._write_receipt(
                receipt,
                bootstrap.tmux_static._receipt_value(
                    component["template"]["revision"],
                    bootstrap.tmux_static._block(
                        component["template"]["revision"], bootstrap.tmux_static._template_body()
                    )[1],
                ),
            )
            target.write_bytes(before + before)
            duplicate = target.read_bytes()
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                with self.assertRaisesRegex(bootstrap.BootstrapError, "duplicated"):
                    bootstrap.static_operation(args, "tmux-config", component, "upgrade")
            self.assertEqual(target.read_bytes(), duplicate)

            target.unlink()
            target.symlink_to(root / "unsafe.conf")
            with patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"):
                with self.assertRaisesRegex(bootstrap.BootstrapError, "symbolic-link"):
                    bootstrap.static_operation(args, "tmux-config", component, "install")

    def test_tmux_discover_exposes_static_state_separately(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args, component, codex_home, home = self.tmux_fixture(root)
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            args.catalog = bootstrap.DEFAULT_CATALOG
            with (
                patch.object(bootstrap.tmux_static.shutil, "which", return_value="/usr/bin/tmux"),
                patch.object(bootstrap, "host", SimpleNamespace(detect_host=lambda: {"installers": {}})),
            ):
                inventory = bootstrap.discover(args, catalog)
            observed = inventory["components"]["tmux-config"]
            self.assertEqual(observed["status"], "missing")
            self.assertEqual(observed["static_state"], "absent")
            self.assertEqual(inventory["static"]["assets"]["tmux-config"]["state"], "absent")
            self.assertNotIn("configuration", inventory["static"])

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
                        "reconcile": "not-applicable",
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
            self.trust_collection(destination)

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
                    "actions": {"install": "native-owner", "configure": "not-applicable", "upgrade": "native-owner", "uninstall": "managed", "verify": "managed", "reconcile": "not-applicable"},
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

            with patch.object(bootstrap, "prepare_staged_collection"):
                bootstrap.replace_staged_collection(args, catalog)

            self.assertEqual(bootstrap.probe_component(component, root / "codex", str(destination))[0], "match")

        args.command = "upgrade"
        with self.assertRaisesRegex(bootstrap.BootstrapError, "native-owner"):
            bootstrap.run_lifecycle(args, catalog)

    def test_explicit_replace_staged_bootstraps_exact_legacy_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "skills" / "pennix-skills"
            staging = root / "skills" / ".pennix-skills-stage"
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            component = catalog["components"]["pennix-skills"]
            for parent in (destination, staging):
                for name in bootstrap.collection_skill_names(component):
                    skill = parent / name
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

            with patch.object(bootstrap, "prepare_staged_collection"):
                bootstrap.replace_staged_collection(args, catalog)

            self.assertEqual(bootstrap.skills_install.collection_receipt_state(destination), "match")

    def test_post_install_actions_are_a_closed_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary) / "pennix-skills"
            skill = staging / "grok-search"
            (skill / "bin").mkdir(parents=True)
            (skill / "package.json").write_text("{}\n", encoding="utf-8")
            (skill / "package-lock.json").write_text("{}\n", encoding="utf-8")
            command = skill / "bin" / "grok-search"
            command.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
            component = catalog["components"]["pennix-skills"]
            with (
                patch.object(bootstrap.shutil, "which", return_value="/usr/bin/npm"),
                patch.object(bootstrap.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run,
            ):
                bootstrap.prepare_staged_collection(component, staging)
            self.assertEqual(run.call_args.args[0], ["/usr/bin/npm", "ci", "--omit=dev", "--ignore-scripts"])
            self.assertTrue(command.stat().st_mode & 0o111)

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
            self.trust_collection(destination)
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
            allowed_runtime = {"node_modules"} if name == "grok-search" else set()
            entries = {entry.name for entry in (SKILL_ROOT.parent / name).iterdir()}
            self.assertFalse(entries & (forbidden - allowed_runtime), name)

    def test_default_catalog_accepts_scoped_npm_packages(self) -> None:
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        self.assertEqual(catalog["components"]["fastctx"]["package"]["name"], "@pennixrv/fastctx")
        self.assertEqual(catalog["components"]["fastctx"]["replaces"], ["fastctx"])
        self.assertEqual(catalog["components"]["codex-cli"]["package"]["source"], "aur")
        self.assertEqual(catalog["components"]["codex-cli"]["version_policy"], "repository-latest")
        self.assertNotIn("approved_version", catalog["components"]["codex-cli"])
        self.assertEqual(catalog["components"]["ponytail-plugin"]["plugin"]["id"], "ponytail@ponytail")
        self.assertEqual(catalog["components"]["trellis-cli"]["approved_version"], "0.7.0-beta.12")
        self.assertEqual(catalog["components"]["trellis-cli"]["package"]["tag"], "beta")

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

    def test_pacman_package_queries_require_an_exact_name(self) -> None:
        with patch.object(bootstrap.shutil, "which", return_value="/usr/bin/pacman"):
            with patch.object(
                bootstrap.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="openai-codex-bin\n", stderr=""),
            ):
                self.assertFalse(bootstrap.installed_pacman_package("openai-codex"))
                self.assertTrue(bootstrap.installed_pacman_package("openai-codex-bin"))

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
        tmux = catalog["components"]["tmux-config"]
        self.assertEqual(tmux["delivery"], "static")
        self.assertEqual(tmux["adapter"], "tmux-config")
        self.assertEqual(tmux["template"]["name"], "tmux.conf.install")
        self.assertEqual(
            (SKILL_ROOT / "templates" / "tmux.conf.install").read_text(encoding="utf-8").splitlines(),
            [
                'set -g default-terminal "xterm-256color"',
                'set-option -ga terminal-overrides ",xterm-256color:Tc"',
                'set -g window-style "fg=#F5F5F5,bg=#1E1E1E"',
                'set -g window-active-style "fg=#F5F5F5,bg=#1E1E1E"',
            ],
        )
        self.assertEqual(catalog["components"]["cch-status"]["actions"]["install"], "native-owner")
        self.assertEqual(catalog["components"]["pennix-skills"]["delivery"], "collection")
        self.assertEqual(catalog["components"][bootstrap.STATE_COMPONENT]["actions"]["reconcile"], "managed")

    def test_non_managed_action_is_rejected_before_adapter(self) -> None:
        args = SimpleNamespace(command="install", component="cch-status", yes=True)
        catalog = bootstrap.load_catalog(bootstrap.DEFAULT_CATALOG)
        with self.assertRaisesRegex(bootstrap.BootstrapError, "native-owner"):
            bootstrap.run_lifecycle(args, catalog)


if __name__ == "__main__":
    unittest.main()
