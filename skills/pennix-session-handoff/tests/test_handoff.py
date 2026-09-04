#!/usr/bin/env python3
"""Regression tests for the bounded Pennix session-handoff helper."""

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
        root = Path(tempfile.mkdtemp(prefix="pennix-session-handoff-"))
        (root / ".trellis/scripts").mkdir(parents=True)
        selected = "None" if task_dir is None else repr({"id": "fixture-task", "dir": task_dir, "status": "in_progress"})
        (root / ".trellis/scripts/task.py").write_text("import json\nprint(json.dumps({'current_task': " + selected + "}))\n", encoding="utf-8")
        return root

    def make_git_root(self, *, with_task: bool = False) -> Path:
        root = self.make_root(".trellis/tasks/demo" if with_task else None)
        (root / "evidence.md").write_text("verified fixture\n", encoding="utf-8")
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

    def make_rollout(self) -> Path:
        handle = tempfile.NamedTemporaryFile("wb", suffix=".jsonl", delete=False)
        path = Path(handle.name)
        records = [
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:00Z", "payload": {"type": "user_message", "message": "审查 `pennix-session-handoff`，不要复制 rollout。"}},
            {"type": "response_item", "timestamp": "2026-09-04T01:00:01Z", "payload": {"type": "reasoning", "encrypted_content": "must not enter handoff"}},
            {"type": "compacted", "timestamp": "2026-09-04T01:00:01Z", "payload": {"type": "compacted", "replacement_history": ["must not be expanded"]}},
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:02Z", "payload": {"type": "agent_message", "message": "已完成本地核验，下一步运行测试。"}},
            {"type": "response_item", "timestamp": "2026-09-04T01:00:03Z", "payload": {"type": "function_call", "name": "shell", "call_id": "call-1", "arguments": "hidden"}},
            {"type": "response_item", "timestamp": "2026-09-04T01:00:04Z", "payload": {"type": "function_call_output", "call_id": "call-1", "output": "passed"}},
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:05Z", "payload": {"type": "user_message", "message": "`pennix-session-handoff` 已确认，继续提交。"}},
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:06Z", "payload": {"type": "user_message", "message": "token th-abcdefghijklmnopqrstuvwx 不应出现在交接中。"}},
        ]
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n")
            if record is records[1]:
                handle.write(b"\0" * 16 + b"\n")
        handle.close()
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def run_cli(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", str(SCRIPT), "--project-root", str(root), *arguments], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def make_request(self, root: Path, rollout: Path | None = None) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        request = Path(handle.name)
        json.dump({
            "session_label": "fixture handoff", "facts": ["fixture task and Git state were checked"],
            "evidence_paths": ["evidence.md"], "next_action": "continue the fixture task", "blockers": [], "risks": [],
            "validation": [{"command": "fixture check", "result": "passed"}],
            "rollout": {"path": str(rollout or self.make_rollout()), "session_id": "fixture-session"},
        }, handle, ensure_ascii=False)
        handle.write("\n")
        handle.close()
        self.addCleanup(request.unlink, missing_ok=True)
        return request

    @staticmethod
    def handoff_path_from(stdout: str) -> str:
        return json.loads(stdout)["handoff_path"]

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

    def test_cli_requires_explicit_request_before_writing(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        request = self.make_request(root)
        result = self.run_cli(root, "write", "--request", str(request))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"status": "recovery_required"', result.stdout)
        self.assertFalse((root / handoff.HANDOFFS).exists())

    def test_cli_write_validate_and_rollout_candidates(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        destination = root / relative
        self.assertRegex(relative, r"^\.trellis/session-handoffs/\d{8}T\d{12}Z/session-handoff\.json$")
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(destination.parent.stat().st_mode), 0o700)
        payload = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 4)
        self.assertEqual(payload["handoff_id"], Path(relative).parts[-2])
        self.assertTrue(any(item["kind"] == "user" for item in payload["conversation"]["candidates"]))
        self.assertEqual([item["state"] for item in payload["conversation"]["timeline"]], ["corrected", "accepted"])
        self.assertEqual(payload["conversation"]["timeline"][1]["supersedes_event_index"], 1)
        self.assertEqual(payload["conversation"]["coverage"]["omissions"][0]["kind"], "nul_padding_record")
        self.assertEqual(payload["conversation"]["coverage"]["excluded"]["compacted"], 1)
        self.assertEqual(len(payload["conversation"]["coverage"]["compacted_spans"]), 1)
        self.assertNotIn("must not enter handoff", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("th-abcdefghijklmnopqrstuvwx", json.dumps(payload, ensure_ascii=False))
        validated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "ready")

    def test_rollout_append_after_capture_remains_ready(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        with rollout.open("ab") as handle:
            handle.write(b'{"type":"event_msg","payload":{"type":"task_complete"}}\n')
        validated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(validated.stdout)["status"], "ready")

    def test_rollout_prefix_mutation_and_evidence_drift_invalidate_receipt(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        raw = rollout.read_bytes()
        rollout.write_bytes(b" " + raw[1:])
        mutated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(mutated.stdout)["status"], "changed")

        written = self.run_cli(root, "write", "--request", str(self.make_request(root, self.make_rollout())), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        (root / "evidence.md").write_text("changed\n", encoding="utf-8")
        drifted = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(drifted.stdout)["status"], "changed")

    def test_old_fixed_path_is_not_a_valid_package(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        result = self.run_cli(root, "validate", "--handoff", ".trellis/session-handoff.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timestamped handoff package", json.loads(result.stdout)["reason"])


if __name__ == "__main__":
    unittest.main()
