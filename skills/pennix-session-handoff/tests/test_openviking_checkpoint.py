#!/usr/bin/env python3
"""Regression tests for the explicit OpenViking handoff checkpoint."""

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
HANDOFF = SKILL / "scripts" / "handoff.py"
CHECKPOINT = SKILL / "scripts" / "openviking_checkpoint.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handoff = load("handoff", HANDOFF)
checkpoint = load("openviking_checkpoint", CHECKPOINT)


class OpenVikingCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="pennix-ov-checkpoint-"))
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / ".trellis/scripts").mkdir(parents=True)
        task = self.root / ".trellis/tasks/demo"
        task.mkdir(parents=True)
        (task / "task.json").write_text(json.dumps({"id": "fixture-task", "status": "in_progress"}) + "\n", encoding="utf-8")
        (task / "prd.md").write_text("fixture\n", encoding="utf-8")
        (self.root / "evidence.md").write_text("fixture\n", encoding="utf-8")
        (self.root / ".trellis/scripts/task.py").write_text(
            "import json, sys\n"
            "args = sys.argv[1:]\n"
            "if args == ['current', '--json']:\n"
            "    print(json.dumps({'current_task': {'id': 'fixture-task', 'dir': '.trellis/tasks/demo', 'status': 'in_progress'}, 'source': 'session:source'}))\n"
            "elif args and args[0] == 'ownership':\n"
            "    op = args[1]\n"
            "    status = {'quiesce': 'quiescing', 'seal': 'sealed', 'retire-handoff': 'ready', 'status': 'sealed'}[op]\n"
            "    generation = {'quiesce': 0, 'seal': 1, 'retire-handoff': 2, 'status': 1}[op]\n"
            "    print(json.dumps({'status': status, 'generation': generation, 'record_digest': 'sha256:' + 'a' * 64}))\n"
            "else:\n"
            "    raise SystemExit(2)\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.state = self.root / "ov-state.json"
        self.log = self.root / "ov.log"
        fake = self.bin / "ov"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "state_path = os.environ['FAKE_OV_STATE']\n"
            "log_path = os.environ['FAKE_OV_LOG']\n"
            "try:\n"
            "    state = json.load(open(state_path, encoding='utf-8'))\n"
            "except FileNotFoundError:\n"
            "    state = {'archive': False, 'marker': None}\n"
            "args = [arg for arg in sys.argv[1:] if arg not in ('-o', 'json')]\n"
            "with open(log_path, 'a', encoding='utf-8') as handle: handle.write(json.dumps(args) + '\\n')\n"
            "archive = 'viking://user/penn/sessions/cx-fixture-session/history/archive_001'\n"
            "task = 'fixture-task-id'\n"
            "def out(value): print(json.dumps(value)); json.dump(state, open(state_path, 'w', encoding='utf-8'))\n"
            "if args[:2] == ['session', 'get']:\n"
            "    out({'archives': [archive] if state.get('archive') else []})\n"
            "elif args[:2] == ['session', 'get-session-context']:\n"
            "    out({'messages': [state.get('marker')] if state.get('marker') and not state.get('archive') else []})\n"
            "elif args[:2] == ['session', 'add-message']:\n"
            "    state['marker'] = args[args.index('--content') + 1]; out({'ok': True})\n"
            "elif args[:2] == ['session', 'commit']:\n"
            "    state['archive'] = True; out({'archived': True, 'archive_uri': archive, 'task_id': task})\n"
            "elif args[:1] == ['grep']:\n"
            "    out({'matches': [state.get('marker')] if state.get('archive') else []})\n"
            "elif args[:1] == ['read']:\n"
            "    out({'content': state.get('marker', '')})\n"
            "elif args[:2] == ['task', 'list']:\n"
            "    out({'tasks': [{'id': task, 'result': {'archive_uri': archive}}] if state.get('archive') else []})\n"
            "elif args[:2] == ['task', 'status']:\n"
            "    result = {'archive_uri': archive, 'memory_diff_uri': archive + '/memory_diff.json'}\n"
            "    out({'status': os.environ.get('FAKE_OV_TASK_STATUS', 'completed'), 'result': result})\n"
            "else:\n"
            "    raise SystemExit(2)\n",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.old_path = os.environ.get("PATH", "")
        os.environ.update({"PATH": str(self.bin) + os.pathsep + self.old_path, "FAKE_OV_STATE": str(self.state), "FAKE_OV_LOG": str(self.log)})
        self.addCleanup(self.restore_env)

    def restore_env(self) -> None:
        os.environ["PATH"] = self.old_path
        os.environ.pop("FAKE_OV_STATE", None)
        os.environ.pop("FAKE_OV_LOG", None)
        os.environ.pop("FAKE_OV_TASK_STATUS", None)

    def handoff(self, mode: str) -> str:
        rollout = self.root / "rollout.jsonl"
        rollout.write_text(json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "checkpoint"}}) + "\n", encoding="utf-8")
        request = self.root / "request.json"
        request.write_text(json.dumps({
            "session_label": "fixture", "facts": ["checked"], "evidence_paths": ["evidence.md"],
            "next_action": "stop", "blockers": [], "risks": [], "validation": [],
            "memory_projection": {"semantic_capsule": "semantic boundary", "local": [], "archive_refs": [], "openviking": []},
            "rollout": {"path": str(rollout), "session_id": "fixture-session"},
        }), encoding="utf-8")
        written = subprocess.run(["python3", str(HANDOFF), "--project-root", str(self.root), "write", "--request", str(request), "--explicit-user-request"], text=True, stdout=subprocess.PIPE, check=True)
        relative = json.loads(written.stdout)["handoff_path"]
        (self.root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n", encoding="utf-8")
        self.assertEqual(subprocess.run(["python3", str(HANDOFF), "--project-root", str(self.root), "prepare", "--handoff", relative, "--mode", mode]).returncode, 0)
        self.assertEqual(handoff.ownership_operation(self.root, "quiesce", relative, explicit=True)["ownership"]["status"], "quiescing")
        self.assertEqual(handoff.ownership_operation(self.root, "seal", relative, explicit=True, expected_generation=0)["ownership"]["status"], "sealed")
        return relative

    def commands(self) -> list[list[str]]:
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def test_archive_checkpoint_commits_exact_marker_then_retires(self) -> None:
        relative = self.handoff("archive_required")
        result = checkpoint.checkpoint(self.root, relative)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["stage"], "archive_verified")
        commands = self.commands()
        self.assertIn(["session", "add-message", "cx-fixture-session", "--role", "assistant", "--content", "[pennix-handoff-id:" + Path(relative).parts[-2] + "]\n\nPennix formal handoff semantic checkpoint.\n\nsemantic boundary"], commands)
        self.assertIn(["session", "commit", "cx-fixture-session"], commands)
        self.assertIn(["grep", "[pennix-handoff-id:" + Path(relative).parts[-2] + "]", "--uri", result["archive_uri"]], commands)
        self.assertFalse(any("rollout" in " ".join(command) or "http" in " ".join(command) for command in commands))
        self.assertEqual(checkpoint.status(self.root, relative)["status"], "ready")

    def test_convergence_remains_pending_until_its_exact_task_completes(self) -> None:
        relative = self.handoff("convergence_required")
        os.environ["FAKE_OV_TASK_STATUS"] = "running"
        pending = checkpoint.checkpoint(self.root, relative)
        self.assertEqual(pending["status"], "pending")
        self.assertFalse(any(command[:2] == ["session", "commit"] and command[-1] == "again" for command in self.commands()))
        os.environ["FAKE_OV_TASK_STATUS"] = "completed"
        ready = checkpoint.checkpoint(self.root, relative)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["stage"], "converged")
        self.assertEqual(checkpoint.status(self.root, relative)["status"], "ready")

    def test_recovery_reuses_marker_archive_without_another_append_or_commit(self) -> None:
        relative = self.handoff("archive_required")
        handoff_id = Path(relative).parts[-2]
        self.state.write_text(json.dumps({"archive": True, "marker": "[pennix-handoff-id:%s]" % handoff_id}), encoding="utf-8")
        result = checkpoint.checkpoint(self.root, relative)
        self.assertEqual(result["status"], "ready")
        self.assertFalse(any(command[:2] in (["session", "add-message"], ["session", "commit"]) for command in self.commands()))


if __name__ == "__main__":
    unittest.main()
