import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/pennix-siyuan-knowledge/scripts/connection.py"


class SiyuanLifecycleTests(unittest.TestCase):
    def test_record_owner_keeps_codex_configuration_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "codex"
            home.mkdir()
            config = home / "config.toml"
            config.write_text('custom = "keep"\n[mcp_servers.other]\ncommand = "keep"\n')
            env = {**os.environ, "HOME": str(root), "XDG_CONFIG_HOME": str(root / "config"), "CODEX_HOME": str(home)}
            payload = {"target": "siyuan", "values": {"url": "https://notes.example.test/mcp", "default_notebook": "20260101000000-abcdefg"},
                       "secrets": {"api_token": "test-secret-token"}}
            payload["desired_digest"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

            def run(action, value=payload):
                result = subprocess.run([sys.executable, str(SCRIPT), "lifecycle", action, "--json"],
                                        input=json.dumps(value), capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("test-secret-token", result.stdout + result.stderr)
                return json.loads(result.stdout)

            self.assertEqual(run("configure")["state"], "current")
            self.assertEqual(tomllib.loads(config.read_text())["mcp_servers"], {"other": {"command": "keep"}})
            self.assertEqual(run("inspect")["state"], "current")
            run("configure")
            run("unconfigure", {"target": "siyuan"})
            after = tomllib.loads(config.read_text())
            self.assertEqual(after["custom"], "keep")
            self.assertEqual(after["mcp_servers"], {"other": {"command": "keep"}})

    def test_explicit_adoption_requires_identical_connection_and_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "config/pennix-siyuan"
            private.mkdir(parents=True, mode=0o700)
            record = {"schema": 1, "url": "https://notes.example.test/mcp", "api_token": "test-only-token", "default_notebook": "20260101000000-abcdefg"}
            connection = private / "connection.json"
            connection.write_text(json.dumps(record))
            connection.chmod(0o600)
            payload = {"target": "siyuan", "values": {key: record[key] for key in ("url", "default_notebook")}, "secrets": {"api_token": record["api_token"]}}
            payload["desired_digest"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            env = {**os.environ, "HOME": str(root), "XDG_CONFIG_HOME": str(root / "config"), "CODEX_HOME": str(root / "codex")}
            before = connection.read_bytes()
            for adopt, expected in [(False, 2), (True, 0)]:
                payload["adopt_existing"] = adopt
                result = subprocess.run([sys.executable, str(SCRIPT), "lifecycle", "configure", "--json"],
                                        input=json.dumps(payload), capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(connection.read_bytes(), before)
