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

    def test_collection_state_accepts_exact_installed_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills" / "pennix-skills"
            self.make_skill(destination, "alpha")
            self.make_skill(destination, "beta")

            self.assertEqual(MODULE.collection_state({"alpha", "beta"}, destination), "match")

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
