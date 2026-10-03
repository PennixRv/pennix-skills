import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from adapters import cognee_plugin as adapter


class NativeCogneeConfigurationTest(unittest.TestCase):
    def plugin(self, **changes):
        value = {
            "pluginId": adapter.PLUGIN,
            "version": adapter.VERSION,
            "enabled": True,
            "source": {"source": "git", "ref": adapter.REF},
        }
        value.update(changes)
        return value

    def test_state_accepts_only_the_pinned_native_plugin(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            adapter.codex_plugins, "installed_plugin", return_value=self.plugin()
        ):
            self.assertEqual(adapter.state(Path(temporary)), "configured")

            adapter.codex_plugins.installed_plugin.return_value = self.plugin(version="1.7.3")
            self.assertEqual(adapter.state(Path(temporary)), "drifted")

            adapter.codex_plugins.installed_plugin.return_value = None
            self.assertEqual(adapter.state(Path(temporary)), "not-configured")

    def test_configure_does_not_edit_codex_config(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            adapter.codex_plugins, "installed_plugin", return_value=self.plugin()
        ), mock.patch.object(adapter.codex_plugins, "run_json") as run_json:
            adapter.configure(Path(temporary))
            run_json.assert_not_called()

    def test_remove_delegates_to_the_native_owner(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            adapter.codex_plugins, "installed_plugin", return_value=self.plugin()
        ), mock.patch.object(adapter.codex_plugins, "remove_plugin") as remove:
            adapter.remove(Path(temporary))
            remove.assert_called_once_with(Path(temporary), adapter.PLUGIN)


if __name__ == "__main__":
    unittest.main()
