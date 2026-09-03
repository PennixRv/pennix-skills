#!/usr/bin/env python3
"""Regression coverage for the ready-only handoff prompt renderer."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/render_handoff_prompt.py"
SPEC = importlib.util.spec_from_file_location("render_handoff_prompt", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def payload(*, task_path: str | None = None) -> dict[str, object]:
    return {
        "schema_version": 3,
        "kind": "trellis-session-handoff",
        "work_context": {"task": None if task_path is None else {"path": task_path}},
        "pending": {"next_action": "Review the verified issue index before selecting the next task."},
    }


class RenderHandoffPromptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="handoff-prompt-")
        self.root = Path(self.temp.name).resolve()
        handoff = self.root / renderer.HANDOFF_PATH
        handoff.parent.mkdir(parents=True, exist_ok=True)
        handoff.write_text(json.dumps(payload()) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_colocated_skill_helper_is_used(self) -> None:
        completed = SimpleNamespace(returncode=0, stdout=json.dumps({"status": "ready"}), stderr="")
        with mock.patch.object(renderer.subprocess, "run", return_value=completed) as run:
            renderer._read_payload(self.root)
        self.assertEqual(Path(run.call_args.args[0][1]), renderer.SCRIPT_PATH)

    def test_ready_null_task_prompt_is_bounded_and_explains_normal_state(self) -> None:
        completed = SimpleNamespace(returncode=0, stdout=json.dumps({"status": "ready"}), stderr="")
        with mock.patch.object(renderer.subprocess, "run", return_value=completed):
            prompt = renderer._read_payload(self.root)
        rendered = renderer.render(self.root, prompt)
        self.assertIn("无活动 task（正常", rendered)
        self.assertIn("只有 receipt 为 `ready` 才继续", rendered)
        self.assertIn("`$session-handoff`", rendered)
        self.assertIn("`$trellis-start`", rendered)
        self.assertLess(len(rendered.encode("utf-8")), 2048)

    def test_ready_task_path_is_rendered_as_navigation_data(self) -> None:
        handoff = self.root / renderer.HANDOFF_PATH
        handoff.write_text(json.dumps(payload(task_path=".trellis/tasks/demo")) + "\n", encoding="utf-8")
        completed = SimpleNamespace(returncode=0, stdout=json.dumps({"status": "ready"}), stderr="")
        with mock.patch.object(renderer.subprocess, "run", return_value=completed):
            rendered = renderer.render(self.root, renderer._read_payload(self.root))
        self.assertIn('task=".trellis/tasks/demo"', rendered)
        self.assertIn("不覆盖新用户指令", rendered)
        self.assertIn("`$trellis-continue`", rendered)

    def test_non_ready_receipt_never_emits_a_prompt(self) -> None:
        completed = SimpleNamespace(returncode=2, stdout=json.dumps({"status": "changed"}), stderr="")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(renderer.subprocess, "run", return_value=completed), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = renderer.main(["--project-root", str(self.root)])
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("not ready: changed", stderr.getvalue())

    def test_invalid_runtime_output_does_not_leak_its_content(self) -> None:
        completed = SimpleNamespace(returncode=1, stdout="secret response", stderr="secret diagnostic")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(renderer.subprocess, "run", return_value=completed), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = renderer.main(["--project-root", str(self.root)])
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn("secret", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
