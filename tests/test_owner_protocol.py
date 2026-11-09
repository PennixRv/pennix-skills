import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OwnerProtocolTests(unittest.TestCase):
    def test_validate_has_no_filesystem_effect_and_execution_is_bound(self):
        cases = [
            ("siyuan", "pennix-siyuan-knowledge", {"url": "https://notes.example.test/mcp", "default_notebook": "20260101000000-abcdefg"}, {"api_token": "synthetic-secret"}),
            ("hikari", "pennix-tavily-search", {"base_url": "https://hikari.example.test"}, {"token": "th-abcd-123456789012"}),
        ]
        for target, skill, values, secrets in cases:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                env = {"PATH": os.environ.get("PATH", ""), "HOME": directory,
                       "XDG_CONFIG_HOME": str(root / "config"), "CODEX_HOME": str(root / "codex")}
                canonical = {"target": target, "values": values, "secrets": secrets}
                payload = {**canonical, "desired_digest": hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                           "operation": "configure", "operation_id": "owner-probe"}
                command = [sys.executable, str(ROOT / "skills" / skill / "scripts/connection.py"), "lifecycle"]
                def run(action):
                    result = subprocess.run([*command, action, "--json"], input=json.dumps(payload), text=True,
                                            capture_output=True, env=env, timeout=10)
                    self.assertNotIn(next(iter(secrets.values())), result.stdout + result.stderr)
                    return result, json.loads(result.stdout)
                result, reply = run("validate")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(reply["effect"], "none")
                self.assertEqual(reply["protocol_version"], 1)
                self.assertEqual(list(root.iterdir()), [])
                result, reply = run("configure")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(reply["effect"], "changed")
                self.assertEqual(reply["operation_id"], "owner-probe")
                result, reply = run("configure")
                self.assertEqual(result.returncode, 0)
                self.assertEqual(reply["effect"], "none")
                result, reply = run("unconfigure")
                self.assertEqual(result.returncode, 0)
                self.assertEqual(reply["effect"], "changed")
                result, reply = run("configure")
                self.assertEqual(result.returncode, 0)
                config = (root / "config" / "pennix-siyuan" / "connection.json" if target == "siyuan"
                          else root / "config" / "tavily-hikari-cli" / "config.json")
                config.unlink()
                result, reply = run("inspect")
                self.assertEqual(reply["state"], "orphaned")
                self.assertTrue(reply["owned"])
                result, reply = run("unconfigure")
                self.assertEqual(result.returncode, 0)
                self.assertEqual(reply["effect"], "changed")
                payload["desired_digest"] = "invalid"
                result, reply = run("configure")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(reply["effect"], "none")
