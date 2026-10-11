import json
import os
from pathlib import Path
import shlex
import sys
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapters import siyuan, configuration


class ConnectionTests(unittest.TestCase):
    def test_interpreter_alias_is_ready_without_mutating_records(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "codex"; home.mkdir()
            helper = siyuan.helper_path(home); helper.parent.mkdir(parents=True); helper.write_text("fixture")
            config = home / "config.toml"
            config.write_text('model = "keep"\n')
            alias = base / "python alias"
            alias.symlink_to(sys.executable)
            values = ["https://notes.example/mcp", "20261004222305-tq7bml3", "fake-token"]
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(base / "config")}), patch.object(configuration, "_read_tty", side_effect=values):
                self.assertEqual(siyuan.configure(home), "configured")
                command = shlex.join([sys.executable, str(helper)])
                alias_command = shlex.join([str(alias), str(helper)])
                config.write_text(config.read_text().replace(json.dumps(command), json.dumps(alias_command)))
                config_bytes = config.read_bytes()
                record = base / "config/pennix-siyuan/connection.json"
                record_bytes = record.read_bytes()
                with patch.object(configuration, "_read_tty") as prompt:
                    self.assertEqual(siyuan.target_state(home), "configured")
                    prompt.assert_not_called()
                self.assertEqual(config.read_bytes(), config_bytes)
                self.assertEqual(record.read_bytes(), record_bytes)

    def test_changed_or_unverifiable_helper_command_fails_before_input(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "codex"; home.mkdir()
            helper = siyuan.helper_path(home); helper.parent.mkdir(parents=True); helper.write_text("fixture")
            config = home / "config.toml"
            config.write_text('model = "keep"\n')
            other = base / "different-python"; other.write_text("fixture")
            values = ["https://notes.example/mcp", "20261004222305-tq7bml3", "fake-token"]
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(base / "config")}), patch.object(configuration, "_read_tty", side_effect=values):
                self.assertEqual(siyuan.configure(home), "configured")
                original = config.read_text()
                command = shlex.join([sys.executable, str(helper)])
                record = base / "config/pennix-siyuan/connection.json"
                record_bytes = record.read_bytes()
                for changed in (
                    shlex.join([str(other), str(helper)]),
                    shlex.join([sys.executable, str(helper.with_name("other.py"))]),
                    shlex.join([sys.executable, "-I", str(helper)]),
                    shlex.join([str(base / "missing-python"), str(helper)]),
                    shlex.join(["python3", str(helper)]),
                    "'",
                ):
                    with self.subTest(command=changed), patch.object(configuration, "_read_tty") as prompt:
                        config.write_text(original.replace(json.dumps(command), json.dumps(changed)))
                        config_bytes = config.read_bytes()
                        self.assertEqual(siyuan.target_state(home), "blocked")
                        with self.assertRaises(configuration.ConfigurationError):
                            siyuan.configure(home)
                        prompt.assert_not_called()
                        self.assertEqual(config.read_bytes(), config_bytes)
                        self.assertEqual(record.read_bytes(), record_bytes)
                config.write_text(original)
                with patch.object(Path, "samefile", side_effect=PermissionError("fixture")), patch.object(configuration, "_read_tty") as prompt:
                    self.assertEqual(siyuan.target_state(home), "blocked")
                    with self.assertRaises(configuration.ConfigurationError):
                        siyuan.configure(home)
                    prompt.assert_not_called()
                self.assertEqual(config.read_text(), original)
                self.assertEqual(record.read_bytes(), record_bytes)

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
                reordered = observed.replace(siyuan.BEGIN, "fixture-begin").replace(siyuan.END, siyuan.BEGIN).replace("fixture-begin", siyuan.END)
                config.write_text(reordered)
                self.assertEqual(siyuan.target_state(home), "blocked")
                with self.assertRaises(configuration.ConfigurationError): siyuan.configure(home)
                self.assertEqual(config.read_text(), reordered)
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
