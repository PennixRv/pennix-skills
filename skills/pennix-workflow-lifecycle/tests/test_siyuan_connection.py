import json
import os
from pathlib import Path
import sys
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters import siyuan, configuration


class ConnectionTests(unittest.TestCase):
    def test_configure_preserves_config_and_refuses_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "codex"; home.mkdir()
            helper = siyuan.helper_path(home); helper.parent.mkdir(parents=True); helper.write_text("fixture")
            config = home / "config.toml"
            original = 'model = "fixture"\n[mcp_servers.other]\ncommand = "keep"\n'
            config.write_text(original)
            values = ["https://notes.example/mcp", "20261004222305-tq7bml3", "fake-token"]
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(base / "config")}), patch.object(configuration, "_read_tty", side_effect=values):
                self.assertEqual(siyuan.target_state(home), "not-configured")
                self.assertEqual(siyuan.configure(home), "configured")
                observed = config.read_text()
                self.assertTrue(observed.startswith(original))
                self.assertNotIn("fake-token", observed)
                if shutil.which("codex"):
                    parsed = subprocess.run(["codex", "mcp", "list"], env={**os.environ, "CODEX_HOME": str(home)}, capture_output=True, text=True)
                    self.assertEqual(parsed.returncode, 0, parsed.stderr)
                config.write_text(observed.replace("required = false", "required = true"))
                self.assertEqual(siyuan.target_state(home), "blocked")
                with self.assertRaises(configuration.ConfigurationError): siyuan.configure(home)
                self.assertEqual(configuration._read_tty.call_count, 3)
            record = base / "config/pennix-siyuan/connection.json"
            self.assertEqual(record.stat().st_mode & 0o777, 0o600)
            self.assertEqual(record.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(json.loads(record.read_text())["api_token"], "fake-token")

    def test_user_entry_and_unsafe_record_fail_before_input(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex"; home.mkdir()
            (home / "config.toml").write_text('[mcp_servers.siyuan]\nurl="https://keep.example/mcp"\n')
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}), patch.object(configuration, "_read_tty") as prompt:
                with self.assertRaises(configuration.ConfigurationError): siyuan.configure(home)
                prompt.assert_not_called()

    def test_failed_config_write_does_not_leave_new_secret_record(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex"; home.mkdir()
            helper = siyuan.helper_path(home); helper.parent.mkdir(parents=True); helper.write_text("fixture")
            (home / "config.toml").write_text('model="keep"\n')
            values = ["https://notes.example/mcp", "20261004222305-tq7bml3", "fake-token"]
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}), patch.object(configuration, "_read_tty", side_effect=values), patch.object(siyuan.codex_static, "write", side_effect=OSError("fixture failure")):
                with self.assertRaises(configuration.ConfigurationError): siyuan.configure(home)
                self.assertFalse((Path(directory) / "pennix-siyuan/connection.json").exists())
                self.assertEqual((home / "config.toml").read_text(), 'model="keep"\n')


if __name__ == "__main__":
    unittest.main()
