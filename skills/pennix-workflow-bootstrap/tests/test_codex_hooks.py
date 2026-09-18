import importlib.util
import json
import stat
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "adapters" / "codex_hooks.py"
SPEC = importlib.util.spec_from_file_location("codex_hook_registration", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fragment(command: str = "/opt/peon.sh") -> dict:
    return {
        "hooks": {
            "Stop": [
                {
                    "hooks": [
                        {"type": "command", "command": command, "timeout": 5},
                    ]
                }
            ]
        }
    }


class CodexHookRegistrationTest(unittest.TestCase):
    def test_merge_is_idempotent_and_preserves_metadata(self):
        target = {"description": "existing", "hooks": {"Stop": [fragment()["hooks"]["Stop"][0]]}}
        merged, additions = MODULE.merge_hooks(target, fragment())
        self.assertEqual(additions, 0)
        self.assertEqual(merged, target)
        self.assertEqual(merged["description"], "existing")

    def test_merge_adds_new_event_without_mutating_target(self):
        target = {"description": "existing", "hooks": {}}
        merged, additions = MODULE.merge_hooks(target, fragment())
        self.assertEqual(additions, 1)
        self.assertEqual(target, {"description": "existing", "hooks": {}})
        self.assertEqual(merged["hooks"]["Stop"], fragment()["hooks"]["Stop"])

    def test_invalid_fragment_is_rejected(self):
        with self.assertRaises(MODULE.RegistrationError):
            MODULE.validate_hook_config({"hooks": {"Stop": [{"hooks": [{"type": "command"}]}]}}, "fragment", True)

    def test_inline_hook_is_rejected_but_hooks_state_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.toml"
            config.write_text("[hooks.state]\n\ntrusted_hash = \"sha256:x\"\n", encoding="utf-8")
            MODULE.assert_no_inline_hooks(config)
            config.write_text("[hooks.state]\n\n[[hooks.Stop]]\n", encoding="utf-8")
            with self.assertRaises(MODULE.RegistrationError):
                MODULE.assert_no_inline_hooks(config)

    def test_atomic_write_sets_private_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "hooks.json"
            MODULE.write_json_atomic(destination, {"hooks": {}})
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"hooks": {}})

    def test_atomic_write_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "hooks.json"
            target = Path(temporary) / "target.json"
            target.write_text("{}", encoding="utf-8")
            destination.symlink_to(target)
            with self.assertRaises(MODULE.RegistrationError):
                MODULE.write_json_atomic(destination, {"hooks": {}})

    def test_migrate_preview_keeps_config_and_reports_hooks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.toml"
            destination = root / "hooks.json"
            config.write_text(
                "[features]\n"
                "hooks = true\n\n"
                "[hooks.state]\n"
                "[hooks.state.\"sample\"]\n"
                "trusted_hash = \"sha256:x\"\n\n"
                "[[hooks.Stop]]\n"
                "matcher = \"^done$\"\n\n"
                "[[hooks.Stop.hooks]]\n"
                "type = \"command\"\n"
                "command = \"/opt/stop.sh\"\n"
                "timeout = 5\n",
                encoding="utf-8",
            )
            destination.write_text(json.dumps({"hooks": {}}), encoding="utf-8")
            before_config = config.read_text(encoding="utf-8")
            before_destination = destination.read_text(encoding="utf-8")

            result = MODULE.main(
                ["migrate", "--config", str(config), "--dest", str(destination)]
            )

            self.assertEqual(result, 0)
            self.assertEqual(config.read_text(encoding="utf-8"), before_config)
            self.assertEqual(destination.read_text(encoding="utf-8"), before_destination)

    def test_migrate_apply_moves_inline_hooks_and_preserves_hooks_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.toml"
            destination = root / "hooks.json"
            config.write_text(
                "[features]\n"
                "hooks = true\n\n"
                "[hooks.state]\n"
                "[hooks.state.\"sample\"]\n"
                "trusted_hash = \"sha256:x\"\n\n"
                "[[hooks.Stop]]\n"
                "matcher = \"^done$\"\n\n"
                "[[hooks.Stop.hooks]]\n"
                "type = \"command\"\n"
                "command = \"/opt/stop.sh\"\n"
                "timeout = 5\n\n"
                "[projects.\"/workspace\"]\n"
                "trust_level = \"trusted\"\n",
                encoding="utf-8",
            )
            destination.write_text(json.dumps({"description": "keep", "hooks": {}}), encoding="utf-8")

            result = MODULE.main(
                [
                    "migrate",
                    "--config",
                    str(config),
                    "--dest",
                    str(destination),
                    "--apply",
                ]
            )

            self.assertEqual(result, 0)
            migrated = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(migrated["description"], "keep")
            self.assertEqual(migrated["hooks"]["Stop"][0]["matcher"], "^done$")
            remaining = config.read_text(encoding="utf-8")
            self.assertIn("[hooks.state]", remaining)
            self.assertIn('trusted_hash = "sha256:x"', remaining)
            self.assertIn("[projects.\"/workspace\"]", remaining)
            self.assertNotIn("[[hooks.Stop]]", remaining)
            self.assertNotIn("[[hooks.Stop.hooks]]", remaining)

    def test_migrate_apply_restores_existing_destination_when_config_write_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.toml"
            destination = root / "hooks.json"
            config.write_text(
                "[[hooks.Stop]]\n"
                "matcher = \"^done$\"\n\n"
                "[[hooks.Stop.hooks]]\n"
                "type = \"command\"\n"
                "command = \"/opt/stop.sh\"\n",
                encoding="utf-8",
            )
            destination.write_text('{"description":"original","hooks":{}}\n', encoding="utf-8")
            destination.chmod(0o640)
            before_config = config.read_bytes()
            before_destination = destination.read_bytes()
            before_mode = stat.S_IMODE(destination.stat().st_mode)

            with mock.patch.object(
                MODULE,
                "write_text_atomic",
                side_effect=MODULE.RegistrationError("permission denied"),
            ):
                result = MODULE.main(
                    ["migrate", "--config", str(config), "--dest", str(destination), "--apply"]
                )

            self.assertEqual(result, 1)
            self.assertEqual(config.read_bytes(), before_config)
            self.assertEqual(destination.read_bytes(), before_destination)
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), before_mode)

    def test_migrate_apply_removes_new_destination_when_config_write_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.toml"
            destination = root / "hooks.json"
            config.write_text(
                "[[hooks.Stop]]\n"
                "matcher = \"^done$\"\n\n"
                "[[hooks.Stop.hooks]]\n"
                "type = \"command\"\n"
                "command = \"/opt/stop.sh\"\n",
                encoding="utf-8",
            )
            before_config = config.read_bytes()

            with mock.patch.object(
                MODULE,
                "write_text_atomic",
                side_effect=MODULE.RegistrationError("permission denied"),
            ):
                result = MODULE.main(
                    ["migrate", "--config", str(config), "--dest", str(destination), "--apply"]
                )

            self.assertEqual(result, 1)
            self.assertEqual(config.read_bytes(), before_config)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
