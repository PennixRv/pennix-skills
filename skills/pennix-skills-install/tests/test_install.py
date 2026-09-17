import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "install.py"
SOURCE_ROOT = Path(__file__).parents[3]
SPEC = importlib.util.spec_from_file_location("pennix_skills_install", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class InstallSkillsTest(unittest.TestCase):
    def make_skill(self, root: Path, name: str) -> Path:
        skill = root / "skills" / name
        (skill / "bin").mkdir(parents=True)
        (skill / "scripts").mkdir(parents=True)
        (skill / "references").mkdir()
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test Skill.\n---\n\n# Test\n",
            encoding="utf-8",
        )
        command = skill / "bin" / "example-command"
        command.write_text("#!/bin/sh\n", encoding="utf-8")
        command.chmod(0o755)
        (skill / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")
        (skill / "references" / "contract.md").write_text("contract\n", encoding="utf-8")
        (skill / "UPSTREAM.md").write_text("upstream\n", encoding="utf-8")
        (skill / "package-lock.json").write_text("{}\n", encoding="utf-8")
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

    def test_source_collection_excludes_retired_parallel_protocol_skills(self):
        names = {name for name, _ in MODULE.discover_skills(SOURCE_ROOT)}

        self.assertTrue(
            {
                "grok-search",
                "pennix-fastctx-routing",
                "pennix-fastctx-setup",
                "pennix-trellis-setup",
                "pennix-workflow-routing",
            }.issubset(names)
        )
        self.assertNotIn("trellis-research-record", names)
        self.assertFalse({"parallel-work", "evidence-report", "review-gate"} & names)

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
            self.assertTrue((destination / "beta" / "UPSTREAM.md").is_file())
            self.assertTrue((destination / "beta" / "package-lock.json").is_file())
            self.assertTrue(os.access(destination / "beta" / "bin" / "example-command", os.X_OK))
            self.assertFalse((destination / "alpha" / "test").exists())
            self.assertFalse((destination / "alpha" / ".git").exists())
            self.assertFalse((destination / "obsolete").exists())

    def test_destination_must_be_collection_root(self):
        with self.assertRaises(MODULE.InstallError):
            MODULE.resolve_destination("/tmp/not-a-pennix-install")

    def test_destination_accepts_host_selected_agents_skills_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            alpha = self.make_skill(source, "alpha")
            destination = root / ".agents" / "skills" / "pennix-skills"

            self.assertEqual(MODULE.resolve_destination(str(destination)), destination)
            MODULE.install_skills([("alpha", alpha)], destination)

            self.assertTrue((destination / "alpha" / "SKILL.md").is_file())

    def test_default_destination_remains_codex_home_relative(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(os.environ, {"CODEX_HOME": temporary}, clear=False):
                self.assertEqual(MODULE.default_destination(), Path(temporary) / "skills" / "pennix-skills")

    def test_install_rejects_symbolic_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            alpha = self.make_skill(root, "alpha")
            (alpha / "scripts" / "outside-link").symlink_to("/etc/hosts")
            destination = Path(temporary) / "host" / "skills" / "pennix-skills"

            with self.assertRaises(MODULE.InstallError):
                MODULE.install_skills([("alpha", alpha)], destination)

            self.assertFalse(destination.exists())

    def test_grok_dependency_install_uses_staged_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            package = stage / "grok-search"
            package.mkdir()

            with mock.patch.object(
                MODULE.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
            ) as run:
                MODULE.install_grok_search_dependency(stage)

            run.assert_called_once_with(
                ["npm", "ci", "--omit=dev", "--ignore-scripts"],
                cwd=package,
                check=False,
                text=True,
                stdout=MODULE.subprocess.PIPE,
                stderr=MODULE.subprocess.PIPE,
            )

    def test_dependency_failure_keeps_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            alpha = self.make_skill(root, "alpha")
            destination = Path(temporary) / "host" / "skills" / "pennix-skills"
            (destination / "previous").mkdir(parents=True)

            with mock.patch.object(
                MODULE,
                "install_grok_search_dependency",
                side_effect=MODULE.InstallError("npm unavailable"),
            ):
                with self.assertRaisesRegex(MODULE.InstallError, "npm unavailable"):
                    MODULE.install_skills([("alpha", alpha)], destination)

            self.assertTrue((destination / "previous").is_dir())
            self.assertFalse((destination / "alpha").exists())

    def test_submodule_validation_rejects_uncommitted_content(self):
        source = Path("/tmp/pennix-skills-source")
        submodule_status = " 0123456789012345678901234567890123456789 skills/windsurf-code-search (heads/main)\n"

        with mock.patch.object(MODULE, "run_git", side_effect=[submodule_status, " M SKILL.md\n"]):
            with self.assertRaisesRegex(MODULE.InstallError, "uncommitted changes: skills/windsurf-code-search"):
                MODULE.ensure_submodules(source, initialize=False)


if __name__ == "__main__":
    unittest.main()
