import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("pennix_skills_install", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class InstallSkillsTest(unittest.TestCase):
    def make_skill(self, root: Path, name: str) -> Path:
        skill = root / "skills" / name
        (skill / "scripts").mkdir(parents=True)
        (skill / "references").mkdir()
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test Skill.\n---\n\n# Test\n",
            encoding="utf-8",
        )
        (skill / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")
        (skill / "references" / "contract.md").write_text("contract\n", encoding="utf-8")
        (skill / "test").mkdir()
        (skill / "test" / "development-only.txt").write_text("omit\n", encoding="utf-8")
        (skill / ".git").write_text("gitdir: ignored\n", encoding="utf-8")
        return skill

    def test_discover_rejects_name_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = self.make_skill(root, "alpha")
            (skill / "SKILL.md").write_text(
                "---\nname: beta\ndescription: Test Skill.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaises(MODULE.InstallError):
                MODULE.discover_skills(root)

    def test_install_copies_runtime_assets_and_replaces_managed_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            alpha = self.make_skill(root, "alpha")
            beta = self.make_skill(root, "beta")
            destination = Path(temporary) / "host" / "skills" / "pennix-skills"
            (destination / "obsolete").mkdir(parents=True)
            (destination / "obsolete" / "stale.txt").write_text("stale\n", encoding="utf-8")

            MODULE.install_skills([("alpha", alpha), ("beta", beta)], destination)

            self.assertEqual((destination / "alpha" / "SKILL.md").read_text(encoding="utf-8").splitlines()[1], "name: alpha")
            self.assertTrue((destination / "beta" / "scripts" / "run.py").is_file())
            self.assertTrue((destination / "beta" / "references" / "contract.md").is_file())
            self.assertFalse((destination / "alpha" / "test").exists())
            self.assertFalse((destination / "alpha" / ".git").exists())
            self.assertFalse((destination / "obsolete").exists())

    def test_destination_must_be_collection_root(self):
        with self.assertRaises(MODULE.InstallError):
            MODULE.resolve_destination("/tmp/not-a-pennix-install")

    def test_install_rejects_symbolic_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            alpha = self.make_skill(root, "alpha")
            (alpha / "scripts" / "outside-link").symlink_to("/etc/hosts")
            destination = Path(temporary) / "host" / "skills" / "pennix-skills"

            with self.assertRaises(MODULE.InstallError):
                MODULE.install_skills([("alpha", alpha)], destination)

            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
