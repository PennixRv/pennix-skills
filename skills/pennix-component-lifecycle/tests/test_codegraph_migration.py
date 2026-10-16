from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import lifecycle


COMPONENT = {
    "approved_version": "1.6.2-pennix.1", "probe": "codegraph", "version_args": ["--version"],
    "package": {"source": "npm", "name": "@pennixrv/codegraph", "registry": "https://registry.npmjs.org/", "prefix": "$HOME/.local", "install_owner": "user"},
    "pacman_replacement": {"name": "codegraph-bin", "version": "1.6.2-1"},
}


class CodeGraphMigrationTests(TestCase):
    def test_only_exact_old_version_and_owner_are_accepted(self):
        for version, owner, accepted in [("1.6.2-1", "codegraph-bin", True),
                                          ("1.6.1-1", "codegraph-bin", False),
                                          ("1.6.2-1", "unmanaged", False)]:
            with self.subTest(version=version, owner=owner), \
                 patch.object(lifecycle.shutil, "which", side_effect=lambda name: "/usr/bin/" + name), \
                 patch.object(lifecycle, "installed_package_owner", return_value=owner), \
                 patch.object(lifecycle, "npm_owner_for_command", return_value=None), \
                 patch.object(lifecycle.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=f"codegraph-bin {version}\n")):
                if accepted:
                    self.assertEqual(lifecycle.pacman_replacement(COMPONENT), "codegraph-bin")
                else:
                    with self.assertRaises(lifecycle.BootstrapError):
                        lifecycle.pacman_replacement(COMPONENT)

    def operation(self, candidate, install_exit=0):
        args = SimpleNamespace(codex_home=Path("/tmp/codex-migration-fixture"), destination=None)
        with patch.object(lifecycle.host, "detect_host", return_value={"supported": True, "installers": {"npm": "npm", "official": "pacman"}}), \
             patch.object(lifecycle, "probe_component", side_effect=[("drifted", "1.6.2"), ("match", "1.6.2-pennix.1")]), \
             patch.object(lifecycle, "pacman_replacement", return_value="codegraph-bin"), \
             patch.object(lifecycle, "installed_pacman_package", return_value=False), \
             patch.object(lifecycle, "npm_previous_locations", return_value=[]), \
             patch.object(lifecycle, "installed_npm_packages", return_value={}), \
             patch.object(lifecycle, "npm_global_root", return_value=None), \
             patch.object(lifecycle, "npm_owner_for_command", return_value=None), \
             patch.object(lifecycle.shutil, "which", return_value="/usr/bin/codegraph"), \
             patch.object(lifecycle, "package_candidate_version", return_value=candidate), \
             patch.object(lifecycle, "ensure_npm_user_prefix", return_value=False), \
             patch.object(lifecycle.subprocess, "run", side_effect=[SimpleNamespace(returncode=install_exit), SimpleNamespace(returncode=0)]) as run:
            if candidate != COMPONENT["approved_version"] or install_exit:
                with self.assertRaises(lifecycle.BootstrapError):
                    lifecycle.component_operation(args, {}, "codegraph-cli", COMPONENT, "upgrade")
            else:
                self.assertEqual(lifecycle.component_operation(args, {}, "codegraph-cli", COMPONENT, "upgrade"), "changed")
            return [call.args[0] for call in run.call_args_list]

    def test_registry_must_be_ready_before_removing_old_package(self):
        self.assertEqual(self.operation(None), [])
        self.assertEqual(self.operation("other-version"), [])

    def test_exact_migration_preserves_state_and_stops_after_install_failure(self):
        expected_remove = ["sudo", "pacman", "-R", "--noconfirm", "codegraph-bin"]
        for exit_code in (0, 1):
            calls = self.operation(COMPONENT["approved_version"], exit_code)
            if exit_code:
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][-1], "@pennixrv/codegraph@1.6.2-pennix.1")
                self.assertIn("--ignore-scripts", calls[0])
            else:
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[0][-1], "@pennixrv/codegraph@1.6.2-pennix.1")
                self.assertEqual(calls[1], expected_remove)
