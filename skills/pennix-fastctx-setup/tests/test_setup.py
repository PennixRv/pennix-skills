import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "setup.py"
SPEC = importlib.util.spec_from_file_location("pennix_fastctx_setup", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SetupTest(unittest.TestCase):
    def test_marker_round_trip_preserves_user_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            agents = Path(temporary) / "AGENTS.md"
            agents.write_text("# user\n", encoding="utf-8")

            MODULE.apply_pennix_marker(agents)
            self.assertTrue(agents.read_text(encoding="utf-8").endswith(MODULE.PENNIX_MARKER))

            MODULE.remove_pennix_marker(agents)
            self.assertEqual(agents.read_text(encoding="utf-8"), "# user\n")

    def test_drifted_marker_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            agents = Path(temporary) / "AGENTS.md"
            agents.write_text(f"{MODULE.PENNIX_BEGIN}\nchanged\n{MODULE.PENNIX_END}\n", encoding="utf-8")

            with self.assertRaises(MODULE.SetupError):
                MODULE.apply_pennix_marker(agents)

    def test_linux_asset_mapping(self):
        with mock.patch.object(MODULE.platform, "system", return_value="Linux"), mock.patch.object(
            MODULE.platform, "machine", return_value="x86_64"
        ):
            self.assertEqual(MODULE.release_asset(), "fastctx-x86_64-unknown-linux-gnu.tar.gz")


if __name__ == "__main__":
    unittest.main()
