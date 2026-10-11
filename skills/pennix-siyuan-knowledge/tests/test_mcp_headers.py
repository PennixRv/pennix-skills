"""Behavior checks use fake secrets only and never contact a kernel."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/mcp_headers.py"
spec = importlib.util.spec_from_file_location("headers", SCRIPT)
headers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(headers)


class HeaderTests(unittest.TestCase):
    def test_private_rotation_metadata_and_failure_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "pennix-siyuan"
            root.mkdir(mode=0o700)
            path = root / "connection.json"
            data = {"schema": 1, "url": "https://notes.example/mcp", "api_token": "fake-secret-one", "default_notebook": "20261004222305-tq7bml3"}
            path.write_text(json.dumps(data)); path.chmod(0o600)
            env = {**os.environ, "XDG_CONFIG_HOME": directory}
            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)
            self.assertEqual(json.loads(run().stdout), {"Authorization": "Token fake-secret-one"})
            data["api_token"] = "fake-secret-two"
            path.write_text(json.dumps(data))
            self.assertEqual(json.loads(run().stdout)["Authorization"], "Token fake-secret-two")
            metadata = run("--metadata")
            self.assertEqual(metadata.returncode, 0)
            self.assertNotIn("fake-secret", metadata.stdout + metadata.stderr)
            for key, bad in [("url", "https://user:password@notes.example/mcp"), ("url", "https://notes.example/mcp?key=secret"), ("api_token", "fake-secret\r\nHeader: value")]:
                invalid = {**data, key: bad}; path.write_text(json.dumps(invalid))
                result = run()
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("fake-secret", result.stderr)
            path.write_text(json.dumps(data)); path.chmod(0o644)
            self.assertEqual(run().returncode, 2)
            path.chmod(0o600); root.chmod(0o755)
            self.assertEqual(run().returncode, 2)
            root.chmod(0o700); path.rename(root / "real.json"); path.symlink_to(root / "real.json")
            self.assertEqual(run().returncode, 2)


if __name__ == "__main__":
    unittest.main()
