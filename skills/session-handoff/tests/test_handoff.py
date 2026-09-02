#!/usr/bin/env python3
"""Regression tests for the bounded session-handoff helper."""

from __future__ import annotations

import importlib.util
import json
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
            import shutil

            shutil.rmtree(root)

    def test_payload_shape_rejects_malformed_nested_context(self) -> None:
        root = self.make_root()
        try:
            with self.assertRaisesRegex(handoff.ContractError, "handoff fields"):
                handoff._validate_payload_shape(root, {"schema_version": 3})
        finally:
            import shutil

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
            import shutil

            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
