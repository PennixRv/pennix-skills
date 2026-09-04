#!/usr/bin/env python3
"""Regression tests for the bounded session-handoff helper."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/handoff.py"
SPEC = importlib.util.spec_from_file_location("handoff", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class HandoffTests(unittest.TestCase):
    def make_root(self, task_dir: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp(prefix="session-handoff-"))
        (root / ".trellis/scripts").mkdir(parents=True)
        script = root / ".trellis/scripts/task.py"
        selected = "null" if task_dir is None else json.dumps({
            "id": "fixture-task",
            "dir": task_dir,
            "status": "in_progress",
        })
        script.write_text(
            "import json\nprint(json.dumps({'current_task': " + selected + "}))\n",
            encoding="utf-8",
        )
        return root

    def make_git_root(self, *, with_task: bool = False) -> Path:
        root = self.make_root(
            ".trellis/tasks/demo" if with_task else None,
        )
        evidence = root / "evidence.md"
        evidence.write_text("verified fixture\n", encoding="utf-8")
        if with_task:
            task_dir = root / ".trellis/tasks/demo"
            task_dir.mkdir(parents=True)
            (task_dir / "prd.md").write_text("continue fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        return root

    def run_cli(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--project-root", str(root), *arguments],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def make_request(self, root: Path) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        request = Path(handle.name)
        json.dump({
            "session_label": "fixture handoff",
            "facts": ["fixture task and Git state were checked"],
            "evidence_paths": ["evidence.md"],
            "next_action": "continue the fixture task",
            "blockers": [],
            "risks": [],
            "validation": [{"command": "fixture check", "result": "passed"}],
        }, handle)
        handle.write("\n")
        handle.close()
        self.addCleanup(request.unlink, missing_ok=True)
        return request

    def test_task_symlink_is_rejected_before_resolve(self) -> None:
        root = self.make_root(".trellis/tasks/link")
        try:
            real = root / ".trellis/tasks/real"
            real.mkdir(parents=True)
            (real / "prd.md").write_text("fixture\n", encoding="utf-8")
            (root / ".trellis/tasks/link").symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(handoff.ContractError, "symbolic path"):
                handoff._task_snapshot(root)
        finally:
            shutil.rmtree(root)

    def test_payload_shape_rejects_malformed_nested_context(self) -> None:
        root = self.make_root()
        try:
            with self.assertRaisesRegex(handoff.ContractError, "handoff fields"):
                handoff._validate_payload_shape(root, {"schema_version": 3})
        finally:
            shutil.rmtree(root)

    def test_request_rejects_trellis_runtime_evidence(self) -> None:
        root = self.make_root()
        try:
            runtime = root / ".trellis/.runtime/brief.json"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("{}\n", encoding="utf-8")
            request = root / "request.json"
            request.write_text(json.dumps({
                "session_label": "fixture",
                "facts": ["fixture"],
                "evidence_paths": [".trellis/.runtime/brief.json"],
                "next_action": "continue",
                "blockers": [],
                "risks": [],
                "validation": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(handoff.ContractError, "non-runtime"):
                handoff._request(root, request)
        finally:
            shutil.rmtree(root)

    def test_cli_requires_explicit_request_before_writing(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        request = self.make_request(root)
        result = self.run_cli(root, "write", "--request", str(request))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"status": "recovery_required"', result.stdout)
        self.assertFalse((root / handoff.HANDOFF).exists())

    def test_cli_write_validate_render_and_permissions(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        request = self.make_request(root)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        self.assertIn('"status": "ready"', written.stdout)
        self.assertEqual(stat.S_IMODE(os.stat(root / handoff.HANDOFF).st_mode), 0o600)

        validated = self.run_cli(root, "validate")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertIn('"status": "ready"', validated.stdout)

        rendered = subprocess.run(
            ["python3", str(SKILL / "scripts/render_handoff_prompt.py"), "--project-root", str(root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertIn("`$trellis-start`", rendered.stdout)
        self.assertIn("`$trellis-continue`", rendered.stdout)

    def test_task_drift_invalidates_receipt_and_renderer(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        request = self.make_request(root)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        (root / ".trellis/tasks/demo/prd.md").write_text("changed fixture\n", encoding="utf-8")

        validated = self.run_cli(root, "validate")
        self.assertNotEqual(validated.returncode, 0)
        self.assertIn('"status": "changed"', validated.stdout)
        rendered = subprocess.run(
            ["python3", str(SKILL / "scripts/render_handoff_prompt.py"), "--project-root", str(root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(rendered.returncode, 0)
        self.assertEqual(rendered.stdout, "")
        self.assertIn("not ready: changed", rendered.stderr)


if __name__ == "__main__":
    unittest.main()
