import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/pennix-tavily-search/scripts/connection.py"
TOKEN = "th-" + "test" + "-" + "abcdefghijkl"


class HikariConnectionTests(unittest.TestCase):
    def run_owner(self, root: Path, action: str, payload: dict, **extra_env):
        env = os.environ.copy()
        env.pop("TAVILY_HIKARI_BASE_URL", None)
        env.pop("TAVILY_HIKARI_TOKEN", None)
        env.pop("TAVILY_HIKARI_CONFIG_DIR", None)
        env.pop("TAVILY_HIKARI_CONFIG_FILE", None)
        env.update({"XDG_CONFIG_HOME": str(root / "config"), "HOME": str(root / "home"), **extra_env})
        return subprocess.run(
            [sys.executable, str(SCRIPT), "lifecycle", action, "--json"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    @staticmethod
    def payload():
        values = {"base_url": "https://hikari.example.test/"}
        secrets = {"token": TOKEN}
        canonical = json.dumps(
            {"target": "hikari", "values": values, "secrets": secrets},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return {
            "target": "hikari",
            "values": values,
            "secrets": secrets,
            "desired_digest": hashlib.sha256(canonical).hexdigest(),
        }

    def test_configure_inspect_unconfigure_uses_private_receipt_without_token(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.payload()
            result = self.run_owner(root, "configure", payload)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "current")
            config = root / "config" / "tavily-hikari-cli" / "config.json"
            receipt = config.with_name(".config.json.pennix-lifecycle.json")
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(TOKEN, receipt.read_text(encoding="utf-8"))
            result = self.run_owner(root, "inspect", {"target": "hikari", "desired_digest": payload["desired_digest"]})
            self.assertEqual(json.loads(result.stdout)["state"], "current")
            result = self.run_owner(root, "unconfigure", {"target": "hikari"})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "absent")
            self.assertFalse(config.exists())
            self.assertFalse(receipt.exists())

    def test_external_configuration_is_not_taken_over_or_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config" / "tavily-hikari-cli" / "config.json"
            config.parent.mkdir(parents=True, mode=0o700)
            config.write_text(json.dumps({"baseUrl": "https://external.example.test", "token": TOKEN}), encoding="utf-8")
            config.chmod(0o600)
            result = self.run_owner(root, "inspect", {"target": "hikari"})
            self.assertEqual(json.loads(result.stdout)["state"], "external")
            before = config.read_bytes()
            result = self.run_owner(root, "configure", self.payload())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_bytes(), before)
            result = self.run_owner(root, "unconfigure", {"target": "hikari"})
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(config.exists())

    def test_adoption_preserves_identical_existing_configuration_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.payload()
            payload["values"]["base_url"] = payload["values"]["base_url"].rstrip("/")
            canonical = {key: payload[key] for key in ("target", "values", "secrets")}
            payload["desired_digest"] = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            config = root / "config/tavily-hikari-cli/config.json"
            config.parent.mkdir(parents=True, mode=0o700)
            config.write_text(json.dumps({"baseUrl": payload["values"]["base_url"], "token": TOKEN}, indent=4) + "\n")
            config.chmod(0o600)
            before = config.read_bytes()
            self.assertNotEqual(self.run_owner(root, "configure", payload).returncode, 0)
            payload["adopt_existing"] = True
            result = self.run_owner(root, "configure", payload)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_bytes(), before)

    def test_drift_is_not_removed_and_environment_override_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.payload()
            self.assertEqual(self.run_owner(root, "configure", payload).returncode, 0)
            config = root / "config" / "tavily-hikari-cli" / "config.json"
            config.write_text(json.dumps({"baseUrl": "https://drift.example.test", "token": TOKEN}), encoding="utf-8")
            config.chmod(0o600)
            result = self.run_owner(root, "unconfigure", {"target": "hikari"})
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(config.exists())
            result = self.run_owner(root, "inspect", {"target": "hikari"}, TAVILY_HIKARI_TOKEN=TOKEN)
            self.assertEqual(json.loads(result.stdout)["state"], "environment-override")


if __name__ == "__main__":
    unittest.main()
