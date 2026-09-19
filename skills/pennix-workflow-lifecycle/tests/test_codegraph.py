from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adapters" / "codegraph.py"
SPEC = importlib.util.spec_from_file_location("prepare_project", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
prepare_project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_project)


class PrepareProjectTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q", str(root)], check=True)

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_preview_preserves_existing_config_and_apply_merges_trellis_exclusion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codegraph-setup-") as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            self.init_repo(root)
            config_path = root / "codegraph.json"
            original = {"include": ["src/**"], "exclude": ["build/"], "custom": {"keep": True}}
            config_path.write_text(json.dumps(original), encoding="utf-8")

            preview = self.run_script("--project-root", str(root))

            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn("预览模式：未写入文件", preview.stdout)
            self.assertIn('".trellis/"', preview.stdout)
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8")), original)

            applied = self.run_script("--project-root", str(root), "--apply")

            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertIn("已写入:", applied.stdout)
            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {"include": ["src/**"], "exclude": ["build/", ".trellis/"], "custom": {"keep": True}},
            )

    def test_linked_worktree_is_rejected_without_creating_config(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codegraph-setup-") as temporary:
            base = Path(temporary)
            main = base / "main"
            linked = base / "linked"
            main.mkdir()
            self.init_repo(main)
            (main / "tracked.txt").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(main), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(main), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], check=True)
            subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", str(linked)], check=True)

            result = self.run_script("--project-root", str(linked))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("拒绝 linked Git worktree", result.stderr)
            self.assertFalse((linked / "codegraph.json").exists())

    def test_atomic_write_failure_preserves_original_file_and_cleans_stage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="codegraph-setup-") as temporary:
            root = Path(temporary)
            config_path = root / "codegraph.json"
            config_path.write_text('{"existing": true}\n', encoding="utf-8")

            with mock.patch.object(prepare_project.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    prepare_project.write_atomic(config_path, '{"updated": true}\n')

            self.assertEqual(config_path.read_text(encoding="utf-8"), '{"existing": true}\n')
            self.assertEqual(list(root.glob(".codegraph.json.*")), [])

    def test_unsafe_extra_exclude_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "不接受不安全"):
            prepare_project.validate_pattern("../outside/")


if __name__ == "__main__":
    unittest.main()
