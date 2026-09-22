import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "adapters" / "configuration.py"
SPEC = importlib.util.spec_from_file_location("pennix_configuration", SCRIPT)
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

    def test_cch_uses_a_private_non_json_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            token = root / "cch-token"
            self.private_json(config, '{"endpoint":"https://example.test"}\n')
            self.private_json(token, "not-json-token\n")
            with mock.patch.object(MODULE, "_cch_paths", return_value=(config, token)):
                self.assertEqual(MODULE.target_state("cch-owner", root), "configured")
                token.write_text("", encoding="utf-8")
                self.assertEqual(MODULE.target_state("cch-owner", root), "blocked")

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


if __name__ == "__main__":
    unittest.main()
