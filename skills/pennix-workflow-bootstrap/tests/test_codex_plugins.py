from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import call, patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "adapters" / "codex_plugins.py"
SPEC = importlib.util.spec_from_file_location("pennix_codex_plugins", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


PLUGIN = {
    "id": "fixture@fixture",
    "marketplace": {
        "name": "fixture",
        "source": "https://example.test/fixture.git",
        "ref": "v1.2.3",
        "sparse": ["plugins/fixture"],
    },
}


class CodexPluginTests(unittest.TestCase):
    def test_installed_plugin_uses_native_list_result(self) -> None:
        with patch.object(
            MODULE,
            "run_json",
            return_value={"installed": [{"pluginId": "fixture@fixture", "version": "1.2.3"}]},
        ):
            plugin = MODULE.installed_plugin(Path("/tmp/codex"), "fixture@fixture")
        self.assertEqual(plugin["version"], "1.2.3")

    def test_marketplace_state_compares_source_without_reading_config(self) -> None:
        with patch.object(
            MODULE,
            "run_json",
            return_value={
                "marketplaces": [
                    {
                        "name": "fixture",
                        "marketplaceSource": {"source": "https://example.test/fixture.git"},
                    }
                ]
            },
        ):
            state = MODULE.marketplace_status(Path("/tmp/codex"), "fixture", "https://example.test/fixture.git")
        self.assertEqual(state, "matching-source")

    def test_install_only_adds_an_absent_marketplace(self) -> None:
        home = Path("/tmp/codex")
        with (
            patch.object(MODULE, "marketplace_status", return_value="absent"),
            patch.object(MODULE, "run_json", return_value={}) as run_json,
        ):
            MODULE.install_plugin(home, PLUGIN)

        self.assertEqual(
            run_json.call_args_list,
            [
                call(
                    home,
                    "marketplace",
                    "add",
                    "https://example.test/fixture.git",
                    "--ref",
                    "v1.2.3",
                    "--json",
                    "--sparse",
                    "plugins/fixture",
                ),
                call(home, "add", "fixture@fixture", "--json"),
            ],
        )

    def test_install_refuses_a_preexisting_marketplace(self) -> None:
        with patch.object(MODULE, "marketplace_status", return_value="matching-source"):
            with self.assertRaisesRegex(MODULE.PluginError, "cannot be ref-verified"):
                MODULE.install_plugin(Path("/tmp/codex"), PLUGIN)

    def test_install_removes_new_marketplace_when_plugin_add_fails(self) -> None:
        home = Path("/tmp/codex")
        with (
            patch.object(MODULE, "marketplace_status", side_effect=["absent", "matching-source"]),
            patch.object(MODULE, "installed_plugin", return_value=None),
            patch.object(
                MODULE,
                "run_json",
                side_effect=[{}, MODULE.PluginError("plugin add failed"), {}],
            ) as run_json,
        ):
            with self.assertRaisesRegex(MODULE.PluginError, "plugin add failed"):
                MODULE.install_plugin(home, PLUGIN)

        self.assertEqual(
            run_json.call_args_list[-1],
            call(home, "marketplace", "remove", "fixture", "--json"),
        )


if __name__ == "__main__":
    unittest.main()
