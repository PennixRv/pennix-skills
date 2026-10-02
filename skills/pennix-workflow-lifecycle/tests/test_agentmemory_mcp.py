import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from adapters import agentmemory_mcp as adapter


class NativeMcpConfigurationTest(unittest.TestCase):
    def test_private_env_fixed_pair_and_unrelated_config_survive_reentry(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, {"XDG_DATA_HOME": temporary}):
            root = Path(temporary)
            codex = root / "codex"
            codex.mkdir()
            config = root / "client.env"
            config.write_text("AGENTMEMORY_SECRET=private-test-value\n")
            url = "https://memory.example.test"
            wanted = adapter.expected(config, url)
            for name in ("@agentmemory/mcp", "@agentmemory/agentmemory"):
                package = adapter.directory() / "node_modules" / name / "package.json"
                package.parent.mkdir(parents=True, exist_ok=True)
                package.write_text(json.dumps({"version": adapter.VERSION}))
            (codex / "config.toml").write_text('model = "keep-model"\n')

            def owner_run(arguments, _home):
                if "add" in arguments:
                    (codex / "config.toml").write_text('model = "keep-model"\n[mcp_servers.agentmemory]\ncommand = ' + json.dumps(wanted["command"]) + '\nargs = ' + json.dumps(wanted["args"]) + '\n[mcp_servers.agentmemory.env]\nAGENTMEMORY_FORCE_PROXY = "true"\nAGENTMEMORY_URL = ' + json.dumps(url) + '\n')

            with mock.patch.object(adapter, "_run", side_effect=owner_run):
                adapter.configure(codex, config, url)
                adapter.configure(codex, config, url)
            self.assertEqual(adapter.state(codex, config, url), "configured")
            contents = (codex / "config.toml").read_text()
            self.assertIn('model = "keep-model"', contents)
            self.assertNotIn("private-test-value", contents)
            self.assertEqual(contents.count(adapter.PLUGIN_TABLE), 1)
            (codex / "config.toml").write_text('[mcp_servers.agentmemory]\ncommand = "foreign-client"\n')
            with mock.patch.object(adapter, "_run") as owner:
                with self.assertRaisesRegex(adapter.codex_static.StaticError, "unmanaged"):
                    adapter.configure(codex, config, url)
                owner.assert_not_called()
            (adapter.directory() / "unrelated.txt").write_text("preserve")
            with mock.patch.object(adapter, "_run") as owner:
                with self.assertRaisesRegex(adapter.codex_static.StaticError, "pinned pair"):
                    adapter.remove(codex, config, url)
                owner.assert_not_called()
            self.assertTrue((adapter.directory() / "unrelated.txt").is_file())


if __name__ == "__main__":
    unittest.main()
