import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "adapters" / "configuration.py"
sys.path.insert(0, str(SCRIPT.parents[1]))
SPEC = importlib.util.spec_from_file_location("adapters.configuration", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ConfigurationAdapterTest(unittest.TestCase):
    def private_json(self, path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        os.chmod(path, 0o600)

    def test_private_json_rejects_public_and_linked_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            self.private_json(config, '{"token":"not-printed"}\n')
            self.assertEqual(MODULE._private_json(config)[0], "configured")

            os.chmod(config, 0o644)
            self.assertEqual(MODULE._private_json(config)[0], "blocked")

            link = root / "link.json"
            link.symlink_to(config)
            with self.assertRaises(MODULE.ConfigurationError):
                MODULE._private_json(link)

    def test_profile_reseals_after_a_configuration_contract_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(temporary) / "state")}):
                self.assertEqual(MODULE.load_profile(home, "digest-a"), ("missing", set()))
                self.assertEqual(MODULE.enable_target(home, "digest-a", "grok-search-provider"), {"grok-search-provider"})
                self.assertEqual(MODULE.load_profile(home, "digest-a"), ("match", {"grok-search-provider"}))
                self.assertEqual(MODULE.load_profile(home, "digest-b"), ("stale", {"grok-search-provider"}))
                self.assertEqual(
                    MODULE.enable_target(home, "digest-b", "windsurf-credential"),
                    {"grok-search-provider", "windsurf-credential"},
                )
                self.assertEqual(
                    stat.S_IMODE(MODULE.profile_path(home).stat().st_mode),
                    0o600,
                )
                self.assertNotIn(str(home), str(MODULE.profile_path(home)))

    def test_cch_uses_a_private_non_json_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            token = root / "cch-token"
            self.private_json(config, '{"cch":{"baseUrl":"https://example.test"}}\n')
            self.private_json(token, "not-json-token\n")
            with mock.patch.object(MODULE, "_cch_paths", return_value=(config, token)):
                self.assertEqual(MODULE.target_state("cch-owner", root), "configured")
                token.write_text("", encoding="utf-8")
                self.assertEqual(MODULE.target_state("cch-owner", root), "blocked")

    def test_cch_rejects_invalid_owner_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, token = root / "config.json", root / "cch-token"
            self.private_json(token, "synthetic-token\n")
            with mock.patch.object(MODULE, "_cch_paths", return_value=(config, token)):
                for value in ('{}', '{"endpoint":"https://example.test"}',
                              '{"cch":[]}', '{"cch":{"baseUrl":""}}',
                              '{"cch":{"baseUrl":"not-a-url"}}'):
                    self.private_json(config, value)
                    self.assertEqual(MODULE.target_state("cch-owner", root), "blocked", value)

    def test_grok_marks_unmanaged_owner_configuration_as_drifted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            self.private_json(config, '{"apiKey":"not-printed"}\n')
            with mock.patch.object(MODULE, "_grok_path", return_value=config):
                self.assertEqual(MODULE.target_state("grok-provider", Path(temporary)), "drifted")
                self.private_json(
                    config,
                    '{"apiUrl":"https://example.test","apiKey":"not-printed","pennixLifecycle":1}\n',
                )
                self.assertEqual(MODULE.target_state("grok-provider", Path(temporary)), "configured")

    def test_windsurf_uses_the_validated_collection_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills" / "pennix-skills"
            command = root / "windsurf-code-search" / "bin" / "windsurf-code-search"
            command.parent.mkdir(parents=True)
            command.write_text("#!/bin/sh\necho status=configured\n", encoding="utf-8")
            command.chmod(0o755)
            from adapters import skills_install
            receipt = skills_install._write_receipt(root, skills_install.collection_digest(root))
            os.replace(receipt, skills_install.receipt_path(root))
            with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0, stdout="status=configured\n")) as run:
                self.assertEqual(
                    MODULE.target_state("windsurf-owner", Path(temporary), collection_root=root, collection_member="windsurf-code-search"),
                    "configured",
                )
            self.assertEqual(str(run.call_args.args[0][0]), str(command))
            with mock.patch("shutil.which", return_value="/tmp/attacker/windsurf-code-search"):
                with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0, stdout="status=configured\n")) as run:
                    MODULE.target_state("windsurf-owner", Path(temporary), collection_root=root, collection_member="windsurf-code-search")
                self.assertEqual(str(run.call_args.args[0][0]), str(command))

    def test_windsurf_refuses_missing_or_linked_collection_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills" / "pennix-skills"
            self.assertEqual(
                MODULE.target_state("windsurf-owner", Path(temporary), collection_root=root, collection_member="windsurf-code-search"),
                "unknown",
            )
            command = root / "windsurf-code-search" / "bin" / "windsurf-code-search"
            command.parent.mkdir(parents=True)
            outside = Path(temporary) / "outside"
            outside.write_text("#!/bin/sh\n", encoding="utf-8")
            outside.chmod(0o755)
            command.symlink_to(outside)
            with self.assertRaisesRegex(MODULE.ConfigurationError, "unsafe"):
                MODULE._windsurf_command(root, "windsurf-code-search")




if __name__ == "__main__":
    unittest.main()
