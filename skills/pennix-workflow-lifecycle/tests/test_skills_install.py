import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "adapters" / "skills_install.py"
SPEC = importlib.util.spec_from_file_location("pennix_skills_install", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SkillsCollectionTest(unittest.TestCase):
    def setUp(self) -> None:
        original = MODULE.shutil.which
        patcher = mock.patch.object(MODULE.shutil, "which", side_effect=lambda name, *args, **kwargs:
            None if name == "grok-search" else original(name, *args, **kwargs))
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_skill(self, root: Path, name: str) -> Path:
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test Skill.\n---\n\n# Test\n",
            encoding="utf-8",
        )
        return skill

    def trust_collection(self, destination: Path) -> None:
        staged = MODULE._write_receipt(destination, MODULE.collection_digest(destination))
        os.replace(staged, MODULE.receipt_path(destination))

    def test_frontmatter_accepts_quoted_names_and_multiline_descriptions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary), "alpha")
            (skill / "SKILL.md").write_bytes(b'---\r\nname: "alpha"\r\ndescription: >-\r\n  A useful\r\n  description.\r\n---\r\n# Test\r\n')
            self.assertEqual(MODULE.read_skill_name(skill), "alpha")

    def test_frontmatter_rejects_invalid_metadata_and_duplicate_keys(self) -> None:
        cases = [
            "name: alpha\n", "name: alpha\ndescription: null\n",
            "name: alpha\ndescription: '  '\n", "name: alpha\ndescription: []\n",
            "name: alpha\ndescription: [unfinished\n",
            "name: alpha\nname: alpha\ndescription: valid\n",
            "name: alpha\ndescription: valid\nmetadata:\n  x: 1\n  x: 2\n",
            "name: other\ndescription: valid\n", "name: 42\ndescription: valid\n",
            "- name: alpha\n- description: valid\n",
            "name: alpha\ndescription: !!python/object:builtins.object {}\n",
            "name: alpha\ndescription: " + "x" * 1025 + "\n",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary), "alpha")
            for metadata in cases:
                with self.subTest(metadata=metadata[:60]):
                    (skill / "SKILL.md").write_text("---\n" + metadata + "---\n# Test\n")
                    with self.assertRaises(MODULE.InstallError):
                        MODULE.read_skill_name(skill)
                    self.assertEqual(MODULE.collection_state({"alpha"}, skill.parent), "drifted")

    def test_missing_parser_is_readiness_failure_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary), "alpha")
            with mock.patch.object(MODULE, "yaml", None):
                self.assertEqual(MODULE.format_readiness(), {"status": "missing", "parser": "PyYAML"})
                with self.assertRaisesRegex(MODULE.InstallError, "requires PyYAML"):
                    MODULE.read_skill_name(skill)
                with self.assertRaisesRegex(MODULE.InstallError, "requires PyYAML"):
                    MODULE.collection_state({"alpha"}, skill.parent)

    def test_collection_state_accepts_exact_installed_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "alpha")
            self.make_skill(destination, "beta")

            self.assertEqual(MODULE.collection_state({"alpha", "beta"}, destination), "match")

    def test_receipt_requires_the_exact_private_collection_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "alpha")
            self.trust_collection(destination)
            self.assertEqual(MODULE.collection_receipt_state(destination), "match")

            (destination / "alpha" / "SKILL.md").write_text("changed\n", encoding="utf-8")
            self.assertEqual(MODULE.collection_receipt_state(destination), "drifted")

    def test_exact_legacy_collection_cannot_be_replaced_or_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            destination = root / "pennix-skills"
            staging = root / ".pennix-stage"
            self.make_skill(destination, "alpha")
            self.make_skill(staging, "alpha")

            with self.assertRaisesRegex(MODULE.InstallError, "legacy"):
                MODULE.replace_collection({"alpha"}, staging, destination)
            with self.assertRaisesRegex(MODULE.InstallError, "legacy"):
                MODULE.uninstall_collection({"alpha"}, destination)

    def test_receipt_must_not_be_public(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "alpha")
            self.trust_collection(destination)
            os.chmod(MODULE.receipt_path(destination), 0o644)
            self.assertEqual(MODULE.collection_receipt_state(destination), "drifted")

    def test_collection_state_recognizes_a_safe_partial_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "alpha")
            self.assertEqual(MODULE.collection_state({"alpha", "beta"}, destination), "partial")
            self.assertEqual(MODULE.collection_missing_names({"alpha", "beta"}, destination), ["beta"])
            (destination / "alpha" / "SKILL.md").write_text("drifted\n", encoding="utf-8")
            self.assertEqual(MODULE.collection_state({"alpha"}, destination), "drifted")
            self.assertIsNone(MODULE.collection_missing_names({"alpha"}, destination))

    def test_collection_state_recognizes_an_exact_bootstrap_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "bootstrap")

            self.assertEqual(MODULE.collection_state({"bootstrap", "alpha"}, destination, "bootstrap"), "bootstrap")
            self.assertTrue(MODULE.uninstall_collection({"bootstrap", "alpha"}, destination, "bootstrap"))
            self.assertFalse(destination.exists())

    def test_uninstall_removes_only_an_exact_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "alpha")
            self.trust_collection(destination)

            self.assertTrue(MODULE.uninstall_collection({"alpha"}, destination))
            self.assertFalse(destination.exists())
            self.assertFalse(MODULE.uninstall_collection({"alpha"}, destination))

    def test_uninstall_refuses_an_unrelated_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "unrelated")

            with self.assertRaisesRegex(MODULE.InstallError, "non-exact"):
                MODULE.uninstall_collection({"alpha"}, destination)
            self.assertTrue(destination.exists())

    def test_staged_collection_replaces_a_partial_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            destination = root / "pennix-skills"
            staging = root / ".pennix-stage"
            self.make_skill(destination, "alpha")
            self.make_skill(staging, "alpha")
            self.make_skill(staging, "beta")

            MODULE.replace_collection({"alpha", "beta"}, staging, destination)

            self.assertEqual(MODULE.collection_state({"alpha", "beta"}, destination), "match")
            self.assertEqual(MODULE.collection_receipt_state(destination), "match")

    def test_staged_collection_replaces_known_obsolete_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            destination = root / "pennix-skills"
            staging = root / ".pennix-stage"
            self.make_skill(destination, "alpha")
            self.make_skill(destination, "obsolete")
            self.make_skill(staging, "alpha")

            MODULE.replace_collection({"alpha"}, staging, destination, obsolete_names={"obsolete"})

            self.assertEqual(MODULE.collection_state({"alpha"}, destination), "match")
            self.assertFalse((destination / "obsolete").exists())

    def test_catalog_removal_requires_the_prior_tree_integrity_receipt(self) -> None:
        for drift in (False, True):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "skills"
                destination = root / "pennix-skills"
                staging = root / ".pennix-stage"
                self.make_skill(destination, "alpha")
                self.make_skill(destination, "retired")
                self.trust_collection(destination)
                self.make_skill(staging, "alpha")
                if drift:
                    (destination / "retired" / "unexpected.txt").write_text("unmanaged")
                    with self.assertRaises(MODULE.InstallError):
                        MODULE.replace_collection({"alpha"}, staging, destination)
                    self.assertTrue((destination / "retired").exists())
                else:
                    MODULE.replace_collection({"alpha"}, staging, destination)
                    self.assertFalse((destination / "retired").exists())
                    self.assertEqual(MODULE.collection_receipt_state(destination), "match")

    def test_collection_digest_ignores_python_bytecode_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "pennix-skills"
            skill = destination / "pennix-workflow-lifecycle"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("content\n", encoding="utf-8")
            digest = MODULE.collection_digest(destination)
            scripts = skill / "scripts"
            scripts.mkdir()
            digest = MODULE.collection_digest(destination)
            cache = scripts / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "lifecycle.cpython-313.pyc").write_bytes(b"generated")
            (cache / "nested").mkdir()
            self.assertEqual(MODULE.collection_digest(destination), digest)

    def test_staging_failure_preserves_drifted_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            destination = root / "pennix-skills"
            staging = root / ".pennix-stage"
            self.make_skill(destination, "unrelated")
            self.make_skill(staging, "alpha")

            with self.assertRaisesRegex(MODULE.InstallError, "drifted"):
                MODULE.replace_collection({"alpha"}, staging, destination)
            self.assertTrue((destination / "unrelated" / "SKILL.md").exists())
            self.assertTrue(staging.exists())

    def test_replace_failure_restores_the_previous_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            destination = root / "pennix-skills"
            staging = root / ".pennix-stage"
            self.make_skill(destination, "alpha")
            (destination / "alpha" / "old").write_text("old\n", encoding="utf-8")
            self.trust_collection(destination)
            self.make_skill(staging, "alpha")
            original_replace = os.replace
            calls = 0

            def fail_staging_replace(source: Path | str, target: Path | str) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("staging rename failed")
                original_replace(source, target)

            with mock.patch.object(MODULE.os, "replace", side_effect=fail_staging_replace):
                with self.assertRaisesRegex(OSError, "staging rename failed"):
                    MODULE.replace_collection({"alpha"}, staging, destination)

            self.assertTrue((destination / "alpha" / "old").is_file())
            self.assertTrue(staging.exists())

    def test_late_receipt_failure_restores_tree_and_receipt(self) -> None:
        for existing in (False, True):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "skills"
                destination, staging = root / "pennix-skills", root / ".pennix-stage"
                if existing:
                    self.make_skill(destination, "alpha")
                    (destination / "alpha" / "old").write_text("old")
                    self.trust_collection(destination)
                receipt = MODULE.receipt_path(destination)
                old_receipt = receipt.read_bytes() if existing else None
                self.make_skill(staging, "alpha")
                original_replace = os.replace
                failed = False

                def fail_receipt(source, target):
                    nonlocal failed
                    if Path(target) == receipt and not failed:
                        failed = True
                        raise OSError("late receipt failure")
                    original_replace(source, target)

                with mock.patch.object(MODULE.os, "replace", side_effect=fail_receipt):
                    with self.assertRaisesRegex(OSError, "late receipt failure"):
                        MODULE.replace_collection({"alpha"}, staging, destination)
                self.assertTrue(staging.is_dir())
                self.assertEqual(destination.exists(), existing)
                self.assertEqual(receipt.exists(), existing)
                if existing:
                    self.assertEqual(receipt.read_bytes(), old_receipt)
                    self.assertTrue((destination / "alpha" / "old").is_file())
                    self.assertEqual(MODULE.collection_receipt_state(destination), "match")

    def test_command_install_and_uninstall_are_receipt_owned(self) -> None:
        commands = {"grok-search": {"target": "grok-search/bin/grok-search", "link": ".local/bin/grok-search"}}
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            root = home / ".codex" / "skills"
            destination, staging = root / "pennix-skills", root / ".stage"
            executable = staging / "grok-search" / "bin" / "grok-search"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            (staging / "grok-search" / "SKILL.md").write_text(
                "---\nname: grok-search\ndescription: Test Skill.\n---\n", encoding="utf-8"
            )
            MODULE.replace_collection({"grok-search"}, staging, destination, commands=commands, command_home=home)
            link = home / ".local/bin/grok-search"
            self.assertEqual(link.resolve(), destination / commands["grok-search"]["target"])
            self.assertEqual(MODULE.collection_receipt_state(destination, commands), "match")
            self.assertTrue(MODULE.uninstall_collection({"grok-search"}, destination, commands=commands, command_home=home))
            self.assertFalse(link.exists())
            self.assertFalse(destination.exists())

    def test_unowned_command_path_blocks_replacement_without_touching_it(self) -> None:
        commands = {"grok-search": {"target": "grok-search/bin/grok-search", "link": ".local/bin/grok-search"}}
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            root = home / ".codex" / "skills"
            destination, staging = root / "pennix-skills", root / ".stage"
            command = staging / "grok-search" / "bin" / "grok-search"
            command.parent.mkdir(parents=True)
            command.write_text("#!/bin/sh\n", encoding="utf-8")
            command.chmod(0o755)
            (staging / "grok-search" / "SKILL.md").write_text(
                "---\nname: grok-search\ndescription: Test Skill.\n---\n", encoding="utf-8"
            )
            link = home / ".local/bin/grok-search"
            link.parent.mkdir(parents=True)
            link.write_text("user file\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.InstallError, "unmanaged"):
                MODULE.replace_collection({"grok-search"}, staging, destination, commands=commands, command_home=home)
            self.assertEqual(link.read_text(encoding="utf-8"), "user file\n")
            self.assertFalse(destination.exists())

    def test_link_creation_failure_rolls_back_new_tree_receipt_and_directories(self) -> None:
        commands = {"grok-search": {"target": "grok-search/bin/grok-search", "link": ".local/bin/grok-search"}}
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            destination = home / ".codex/skills/pennix-skills"
            staging = destination.parent / ".stage"
            self.make_skill(staging, "grok-search")
            command = staging / "grok-search/bin/grok-search"
            command.parent.mkdir()
            command.write_text("#!/bin/sh\n")
            command.chmod(0o755)
            with mock.patch.object(Path, "symlink_to", side_effect=OSError("link failure")):
                with self.assertRaisesRegex(OSError, "link failure"):
                    MODULE.replace_collection({"grok-search"}, staging, destination, commands=commands, command_home=home)
            self.assertTrue(staging.is_dir())
            self.assertFalse(destination.exists())
            self.assertFalse(MODULE.receipt_path(destination).exists())
            self.assertFalse((home / ".local").exists())

    def test_schema_one_requires_explicit_migration_and_valid_digest(self) -> None:
        import json
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills/pennix-skills"
            staging = destination.parent / ".stage"
            self.make_skill(destination, "alpha")
            self.make_skill(staging, "alpha")
            receipt = MODULE.receipt_path(destination)
            receipt.write_text(json.dumps({"schema": 1, "destination": destination.name, "digest": MODULE.collection_digest(destination)}))
            receipt.chmod(0o600)
            self.assertEqual(MODULE.collection_receipt_state(destination), "legacy")
            with self.assertRaises(MODULE.InstallError):
                MODULE.replace_collection({"alpha"}, staging, destination)
            MODULE.replace_collection({"alpha"}, staging, destination, allow_legacy=True)
            self.assertEqual(json.loads(receipt.read_text())["schema"], 2)
            self.make_skill(staging, "alpha")
            (destination / "alpha/unowned").write_text("user change")
            with self.assertRaisesRegex(MODULE.InstallError, "drifted"):
                MODULE.replace_collection({"alpha"}, staging, destination, allow_legacy=True)

    def test_upgrade_does_not_adopt_same_target_link_without_receipt_command_proof(self) -> None:
        commands = {"grok-search": {"target": "grok-search/bin/grok-search", "link": ".local/bin/grok-search"}}
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            destination = home / ".codex/skills/pennix-skills"
            staging = destination.parent / ".stage"
            for parent in (destination, staging):
                self.make_skill(parent, "grok-search")
                command = parent / "grok-search/bin/grok-search"
                command.parent.mkdir()
                command.write_text("#!/bin/sh\n")
                command.chmod(0o755)
            self.trust_collection(destination)
            link = home / ".local/bin/grok-search"
            link.parent.mkdir(parents=True)
            link.symlink_to(destination / commands["grok-search"]["target"])
            with self.assertRaisesRegex(MODULE.InstallError, "unmanaged"):
                MODULE.replace_collection({"grok-search"}, staging, destination, commands=commands, command_home=home)
            self.assertTrue(link.is_symlink())
            self.assertTrue(staging.exists())

    def test_destination_must_be_collection_root(self) -> None:
        with self.assertRaises(MODULE.InstallError):
            MODULE.resolve_destination("/tmp/not-a-pennix-install")

    def test_destination_rejects_non_directory_and_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            link = root / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(MODULE.InstallError, "symbolic link"):
                MODULE.resolve_destination(str(link / "skills" / "pennix-skills"))
            destination = root / "skills" / "pennix-skills"
            destination.parent.mkdir()
            destination.write_text("not a directory\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.InstallError, "must be a directory"):
                MODULE.resolve_destination(str(destination))

    def test_default_destination_remains_codex_home_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(os.environ, {"CODEX_HOME": temporary}, clear=False):
                self.assertEqual(MODULE.default_destination(), Path(temporary) / "skills" / "pennix-skills")


if __name__ == "__main__":
    unittest.main()
