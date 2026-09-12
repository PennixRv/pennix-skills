#!/usr/bin/env python3
"""Regression tests for the ready-only paired prompt renderer."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
HANDOFF = SKILL / "scripts/handoff.py"
RENDER = SKILL / "scripts/render_handoff_prompt.py"


class RenderHandoffPromptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="pennix-handoff-prompt-")
        self.root = Path(self.temp.name).resolve()
        (self.root / ".trellis/scripts").mkdir(parents=True)
        (self.root / ".trellis/scripts/task.py").write_text("print('{\"current_task\": null}')\n", encoding="utf-8")
        (self.root / "evidence.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)
        self.rollout = Path(self.temp.name) / "rollout.jsonl"
        self.rollout.write_text(json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "确认 `handoff` 继续。"}}, ensure_ascii=False) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", str(script), "--project-root", str(self.root), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def write(self) -> str:
        request = Path(self.temp.name) / "request.json"
        request.write_text(json.dumps({"session_label": "renderer fixture", "facts": ["verified"], "evidence_paths": ["evidence.md"], "next_action": "continue", "blockers": [], "risks": [], "validation": [], "memory_projection": {"semantic_capsule": "preserved semantic scene", "local": ["research/worktime-memory.md"], "archive_refs": [], "openviking": ["viking://user/penn/memories/experiences"]}, "rollout": {"path": str(self.rollout)}}), encoding="utf-8")
        result = self.run_cli(HANDOFF, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["handoff_path"]

    def test_ready_renderer_creates_colocated_prompt_and_short_index(self) -> None:
        relative = self.write()
        rendered = self.run_cli(RENDER, "--handoff", relative)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertTrue(rendered.stdout.startswith("可直接复制到新会话的短提示词：\n\n```text\n"))
        self.assertTrue(rendered.stdout.endswith("\n```\n"))
        self.assertIn("当前会话位于", rendered.stdout)
        self.assertNotIn("新开 Codex 会话", rendered.stdout)
        self.assertIn("完整阅读", rendered.stdout)
        self.assertIn("不得执行 pending next action", rendered.stdout)
        self.assertIn("$pennix-session-handoff", rendered.stdout)
        prompt = self.root / Path(relative).with_name("session-handoff-prompt.md")
        self.assertTrue(prompt.is_file())
        self.assertIn("Required New-Session Route", prompt.read_text(encoding="utf-8"))
        prompt_text = prompt.read_text(encoding="utf-8")
        self.assertIn("$trellis-finish-work", prompt_text)
        self.assertIn("do not close it from this snapshot", prompt_text)
        self.assertIn("read this entire handoff prompt", prompt_text)
        self.assertIn("preserved semantic scene", prompt_text)
        self.assertIn("viking://user/penn/memories/experiences", prompt_text)
        self.assertIn("Do not execute the pending next action", prompt_text)
        self.assertLess(prompt_text.index("$trellis-start"), prompt_text.index("$trellis-continue"))
        self.assertIn(relative, rendered.stdout)
        self.assertLess(len(rendered.stdout.encode("utf-8")), 2048)
        repeated = self.run_cli(RENDER, "--handoff", relative)
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(repeated.stdout, rendered.stdout)

    def test_invalid_package_never_emits_prompt(self) -> None:
        relative = self.write()
        (self.root / relative).write_text("changed\n", encoding="utf-8")
        rendered = self.run_cli(RENDER, "--handoff", relative)
        self.assertNotEqual(rendered.returncode, 0)
        self.assertEqual(rendered.stdout, "")
        self.assertFalse((self.root / Path(relative).with_name("session-handoff-prompt.md")).exists())
        self.assertIn("handoff is not ready: recovery_required", rendered.stderr)

    def test_pending_lifecycle_never_emits_prompt(self) -> None:
        relative = self.write()
        prepared = self.run_cli(HANDOFF, "prepare", "--handoff", relative, "--mode", "archive_required")
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        rendered = self.run_cli(RENDER, "--handoff", relative)
        self.assertNotEqual(rendered.returncode, 0)
        self.assertEqual(rendered.stdout, "")
        self.assertFalse((self.root / Path(relative).with_name("session-handoff-prompt.md")).exists())
        self.assertIn("lifecycle is not ready: pending", rendered.stderr)


if __name__ == "__main__":
    unittest.main()
