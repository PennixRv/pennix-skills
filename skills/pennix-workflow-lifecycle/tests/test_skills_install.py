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
            self.assertFalse(staging.exists())

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
