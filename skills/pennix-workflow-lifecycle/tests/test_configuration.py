import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "adapters" / "configuration.py"
SPEC = importlib.util.spec_from_file_location("pennix_configuration", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ConfigurationAdapterTest(unittest.TestCase):
    def private_json(self, path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        os.chmod(path, 0o600)

    def test_private_json_rejects_public_and_linked_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            self.private_json(config, '{"token":"not-printed"}\n')
            self.assertEqual(MODULE._private_json(config)[0], "configured")

            os.chmod(config, 0o644)
            self.assertEqual(MODULE._private_json(config)[0], "blocked")

            link = root / "link.json"
            link.symlink_to(config)
            with self.assertRaises(MODULE.ConfigurationError):
                MODULE._private_json(link)

    def test_profile_reseals_after_a_configuration_contract_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(temporary) / "state")}):
                self.assertEqual(MODULE.load_profile(home, "digest-a"), ("missing", set()))
                self.assertEqual(MODULE.enable_target(home, "digest-a", "grok-search-provider"), {"grok-search-provider"})
                self.assertEqual(MODULE.load_profile(home, "digest-a"), ("match", {"grok-search-provider"}))
                self.assertEqual(MODULE.load_profile(home, "digest-b"), ("stale", {"grok-search-provider"}))
                self.assertEqual(
                    MODULE.enable_target(home, "digest-b", "windsurf-credential"),
                    {"grok-search-provider", "windsurf-credential"},
                )
                self.assertEqual(
                    stat.S_IMODE(MODULE.profile_path(home).stat().st_mode),
                    0o600,
                )
                self.assertNotIn(str(home), str(MODULE.profile_path(home)))

    def test_cch_uses_a_private_non_json_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            token = root / "cch-token"
            self.private_json(config, '{"endpoint":"https://example.test"}\n')
            self.private_json(token, "not-json-token\n")
            with mock.patch.object(MODULE, "_cch_paths", return_value=(config, token)):
                self.assertEqual(MODULE.target_state("cch-owner", root), "configured")
                token.write_text("", encoding="utf-8")
                self.assertEqual(MODULE.target_state("cch-owner", root), "blocked")

    def test_grok_marks_unmanaged_owner_configuration_as_drifted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            self.private_json(config, '{"apiKey":"not-printed"}\n')
            with mock.patch.object(MODULE, "_grok_path", return_value=config):
                self.assertEqual(MODULE.target_state("grok-provider", Path(temporary)), "drifted")
                self.private_json(
                    config,
                    '{"apiUrl":"https://example.test","apiKey":"not-printed","pennixLifecycle":1}\n',
                )
                self.assertEqual(MODULE.target_state("grok-provider", Path(temporary)), "configured")

    def test_hindsight_static_and_secret_configuration_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            codex = home / ".codex"
            config = home / ".hindsight" / "coding-agent.json"
            with mock.patch.dict(
                os.environ,
                {"HOME": str(home), "HINDSIGHT_CONFIG": str(config), "XDG_STATE_HOME": str(root / "state")},
                clear=False,
            ):
                self.assertEqual(MODULE.configure_hindsight_static(codex, "https://hindsight.example.test:9999"), "configured")
                data = json.loads(config.read_text(encoding="utf-8"))
                self.assertNotIn("apiToken", data)
                self.assertEqual(stat.S_IMODE(config.stat().st_mode), 0o600)
                self.assertEqual(MODULE.target_state("hindsight-static", codex, {"apiUrl": "https://hindsight.example.test:9999"}), "configured")
                with mock.patch.object(MODULE, "_read_tty", return_value="secret-token"):
                    self.assertEqual(MODULE.configure_hindsight_token(codex), "configured")
                self.assertEqual(MODULE.target_state("hindsight-token", codex), "configured")

    def test_hindsight_static_migrates_an_owned_legacy_reflect_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            codex = home / ".codex"
            config = home / ".hindsight" / "coding-agent.json"
            url = "https://hindsight.example.test:9999"
            legacy = {
                "serverMode": "self-hosted",
                "apiUrl": url,
                "optInOnly": True,
                "autoReflect": True,
                "autoUpdate": False,
                "autoSeed": False,
                "codebaseSurvey": False,
                "gitIngest": "none",
                "retainSessions": True,
            }
            with mock.patch.dict(
                os.environ,
                {"HOME": str(home), "HINDSIGHT_CONFIG": str(config), "XDG_STATE_HOME": str(root / "state")},
                clear=False,
            ):
                self.private_json(config, json.dumps(legacy))
                receipt = MODULE.hindsight_receipt_path(codex)
                self.private_json(
                    receipt,
                    json.dumps({"schema": 1, "path": str(config), "fields": legacy}),
                )
                self.assertEqual(MODULE.configure_hindsight_static(codex, url), "configured")
                data = json.loads(config.read_text(encoding="utf-8"))
                self.assertEqual(data["autoInject"], "pages")
                self.assertEqual(data["pageTriggerType"], "cron")
                self.assertEqual(data["pageTriggerCron"], "H 3 * * *")
                self.assertNotIn("autoReflect", data)
                self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["schema"], 2)

    def test_hindsight_project_registration_is_explicit_and_reversible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            codex = home / ".codex"
            config = home / ".hindsight" / "coding-agent.json"
            project = root / "project"
            (project / ".trellis").mkdir(parents=True)
            (project / ".trellis" / "config.yaml").write_text("session_commit_message: test\n", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"HOME": str(home), "HINDSIGHT_CONFIG": str(config), "XDG_STATE_HOME": str(root / "state")},
                clear=False,
            ):
                MODULE.configure_hindsight_static(codex, "https://hindsight.example.test:9999")
                bank_id = MODULE.register_hindsight_project(codex, project)
                self.assertRegex(bank_id, r"^pennix-project-[0-9a-f]{24}$")
                project_text = (project / ".trellis" / "config.yaml").read_text(encoding="utf-8")
                self.assertIn(f"bank_id: {bank_id}", project_text)
                data = json.loads(config.read_text(encoding="utf-8"))
                self.assertEqual(data["mapPathToBank"][str(project.resolve())], bank_id)
                self.assertEqual(MODULE.unregister_hindsight_project(project), "changed")
                data = json.loads(config.read_text(encoding="utf-8"))
                self.assertNotIn("mapPathToBank", data)


if __name__ == "__main__":
    unittest.main()
