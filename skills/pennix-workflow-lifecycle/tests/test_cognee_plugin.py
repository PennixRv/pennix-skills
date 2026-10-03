import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from adapters import cognee_plugin as adapter


class NativeCogneeConfigurationTest(unittest.TestCase):
    def plugin(self, **changes):
        version, contract = adapter._contract()
        value = {
            "pluginId": contract["id"],
            "version": version,
            "enabled": False,
        }
        value.update(changes)
        return value

    def test_state_requires_pinned_native_plugin_and_disabled_global_policy(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            adapter.codex_plugins, "installed_plugin", return_value=self.plugin()
        ), mock.patch.object(adapter.codex_plugins, "marketplace_status", return_value="matching-ref"), mock.patch.object(adapter, "_content_matches", return_value=True):
            home = Path(temporary)
            (home / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
            self.assertEqual(adapter.state(home), "drifted")
            adapter._ensure_global_disabled(home)
            self.assertEqual(adapter.state(home), "configured")
            self.assertIn('enabled = false', (home / "config.toml").read_text(encoding="utf-8"))

    def test_native_install_enable_is_restored_without_claiming_user_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = home / "config.toml"
            original = '[plugins."cognee@cognee"]\nenabled = false\n'
            config.write_text(original.replace("false", "true"))
            adapter._restore_native_install_policy(home)
            self.assertEqual(config.read_text(), original)


    def test_existing_user_disabled_setting_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = home / "config.toml"
            original = '[plugins."cognee@cognee"]\nenabled = false\n'
            config.write_text(original, encoding="utf-8")
            adapter._ensure_global_disabled(home)
            adapter._remove_global_policy(home)
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_conflicting_enabled_setting_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = home / "config.toml"
            original = '[plugins."cognee@cognee"]\nenabled = true\n'
            config.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(adapter.codex_static.StaticError, "conflicts"):
                adapter._ensure_global_disabled(home)
            self.assertEqual(config.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
