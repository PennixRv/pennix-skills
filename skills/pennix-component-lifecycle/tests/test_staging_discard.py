import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import lifecycle
from adapters import skills_install


class StagingDiscardTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.staging = self.home / "skills/.pennix-skills-stage"
        self.skill = self.staging / "alpha"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("---\nname: alpha\ndescription: Test Skill.\n---\n# Test\n")

    def discard(self, **kwargs):
        return skills_install.discard_staged_collection({"alpha", "beta"}, self.staging, self.home, **kwargs)

    def test_preview_is_read_only_and_execution_preserves_other_assets(self):
        active = self.home / "skills/pennix-skills"
        active.mkdir()
        (active / "keep").write_bytes(b"active")
        receipt = self.home / "skills/.pennix-skills.receipt.json"
        receipt.write_bytes(b"receipt")
        command = self.home / "command"
        command.symlink_to(active / "keep")
        before = {p: skills_install._staging_identity(p.lstat()) for p in [self.staging, *self.staging.rglob("*")]}
        preview = self.discard()
        self.assertEqual(preview["status"], "candidate")
        self.assertEqual(preview["skills"], ["alpha"])
        self.assertEqual(preview["file_bytes"], (self.skill / "SKILL.md").stat().st_size)
        self.assertEqual(before, {p: skills_install._staging_identity(p.lstat()) for p in before})
        result = self.discard(execute=True, expected_digest=preview["digest"])
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["deleted_file_bytes"], preview["file_bytes"])
        self.assertFalse(self.staging.exists())
        self.assertEqual((active / "keep").read_bytes(), b"active")
        self.assertEqual(receipt.read_bytes(), b"receipt")
        self.assertEqual(command.read_bytes(), b"active")

    def test_execution_requires_a_matching_preview(self):
        for digest in (None, "0" * 64):
            with self.subTest(digest=digest), self.assertRaisesRegex(skills_install.InstallError, "digest"):
                self.discard(execute=True, expected_digest=digest)
            self.assertTrue(self.staging.exists())

    def test_content_and_python_cache_changes_invalidate_preview(self):
        cache = self.skill / "__pycache__"
        cache.mkdir()
        bytecode = cache / "test.pyc"
        bytecode.write_bytes(b"old")
        for path in (self.skill / "SKILL.md", bytecode):
            with self.subTest(path=path):
                preview = self.discard()
                path.write_bytes(path.read_bytes() + b"changed")
                with self.assertRaisesRegex(skills_install.InstallError, "digest"):
                    self.discard(execute=True, expected_digest=preview["digest"])
                self.assertTrue(path.exists())

    def test_replaced_root_invalidates_preview(self):
        preview = self.discard()
        old = self.staging.with_name("old")
        self.staging.rename(old)
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_bytes((old / "alpha/SKILL.md").read_bytes())
        with self.assertRaisesRegex(skills_install.InstallError, "digest"):
            self.discard(execute=True, expected_digest=preview["digest"])
        self.assertTrue(self.staging.exists())
        self.assertTrue(old.exists())

    def test_wrong_home_active_directory_and_path_alias_are_rejected(self):
        paths = [self.home / "skills/pennix-skills", self.home / "other/.pennix-skills-stage",
                 self.staging / "alpha/.."]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
            with self.subTest(path=path), self.assertRaises(skills_install.InstallError):
                skills_install.discard_staged_collection({"alpha"}, path, self.home, execute=True)
            self.assertTrue(path.exists())

    def test_symlinks_are_rejected_including_inside_python_cache(self):
        cache = self.skill / "__pycache__"
        cache.mkdir()
        for path in (self.staging / "link", cache / "link"):
            path.symlink_to(self.home)
            with self.subTest(path=path), self.assertRaisesRegex(skills_install.InstallError, "symbolic link"):
                self.discard()
            path.unlink()
        alias = self.home / "skills/.pennix-skills-stage-alias"
        alias.symlink_to(self.staging, target_is_directory=True)
        with self.assertRaisesRegex(skills_install.InstallError, "symbolic link"):
            skills_install.discard_staged_collection({"alpha"}, alias, self.home)

    def test_unknown_entries_invalid_frontmatter_and_special_files_are_rejected(self):
        unknown = self.staging / "unrelated"
        unknown.write_text("do not delete")
        with self.assertRaisesRegex(skills_install.InstallError, "valid Pennix"):
            self.discard()
        unknown.unlink()
        fifo = self.skill / "fifo"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(skills_install.InstallError, "non-regular"):
            self.discard()
        fifo.unlink()
        (self.skill / "SKILL.md").write_text("invalid")
        with self.assertRaisesRegex(skills_install.InstallError, "valid Pennix"):
            self.discard()

    def test_foreign_owner_is_rejected_without_deletion(self):
        with mock.patch.object(skills_install.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaisesRegex(skills_install.InstallError, "owner"):
                self.discard(execute=True)
        self.assertTrue(self.staging.exists())

    def test_changes_during_validation_or_before_delete_are_rejected(self):
        preview = self.discard()
        snapshot = skills_install._staging_snapshot
        for change_at in (2, 3):
            calls = 0

            def changed(path):
                nonlocal calls
                calls += 1
                value = snapshot(path)
                return {**value, "digest": "changed"} if calls == change_at else value

            with self.subTest(change_at=change_at), mock.patch.object(skills_install, "_staging_snapshot", side_effect=changed):
                with self.assertRaisesRegex(skills_install.InstallError, "changed"):
                    self.discard(execute=True, expected_digest=preview["digest"])
            self.assertTrue(self.staging.exists())

    def test_unsupported_delete_and_native_failure_are_reported_without_retry(self):
        preview = self.discard()
        with mock.patch.object(skills_install.shutil.rmtree, "avoids_symlink_attacks", False):
            with self.assertRaisesRegex(skills_install.InstallError, "cannot safely"):
                self.discard(execute=True, expected_digest=preview["digest"])
        with mock.patch.object(skills_install.shutil, "rmtree", side_effect=PermissionError("native failure")) as delete:
            delete.avoids_symlink_attacks = True
            with self.assertRaisesRegex(skills_install.InstallError, "remaining target.*native failure"):
                self.discard(execute=True, expected_digest=preview["digest"])
            self.assertEqual(delete.call_count, 1)
        self.assertTrue(self.staging.exists())

    def test_cli_preview_uses_selected_catalog_without_global_discovery(self):
        name = "pennix-workflow-routing"
        self.skill.rename(self.staging / name)
        (self.staging / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test Skill.\n---\n")
        output = io.StringIO()
        with mock.patch.object(lifecycle, "assert_supported_host"), \
                mock.patch.object(lifecycle, "discover", side_effect=AssertionError("global discovery")), \
                contextlib.redirect_stdout(output):
            code = lifecycle.main(["discard-staged", "--component", "pennix-skills", "--staging",
                                   str(self.staging), "--codex-home", str(self.home)])
        self.assertEqual(code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["operation"], "discard-staged")
        self.assertEqual(result["status"], "candidate")
        self.assertTrue(self.staging.exists())
        output = io.StringIO()
        with mock.patch.object(lifecycle, "assert_supported_host"), contextlib.redirect_stdout(output):
            code = lifecycle.main(["discard-staged", "--component", "pennix-skills", "--staging",
                                   str(self.staging), "--codex-home", str(self.home),
                                   "--yes", "--expected-digest", result["digest"]])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "executed")
        self.assertFalse(self.staging.exists())

    def test_cli_rejects_unsupported_selectors_without_deletion(self):
        for extra in ([], ["--component", "pnpm"], ["--component", "pennix-skills-extra"],
                      ["--component", "pennix-skills", "--destination", str(self.staging)]):
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()):
                code = lifecycle.main(["discard-staged", "--staging", str(self.staging), "--yes", *extra])
            self.assertEqual(code, 2)
            self.assertTrue(self.staging.exists())


if __name__ == "__main__":
    unittest.main()
