#!/usr/bin/env python3
"""Regression tests for the Pennix session-handoff helper."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock


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
        (root / ".trellis/scripts/task.py").write_text("import json, os\nprint(json.dumps({'current_task': " + selected + ", 'source': 'none', 'session_source': 'session:' + os.environ.get('FIXTURE_TARGET', 'source')}))\n", encoding="utf-8")
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

    def make_request(self, root: Path, rollout: Path | None = None, capsule: str = "verified fixture decisions and risks") -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        request = Path(handle.name)
        json.dump({
            "session_label": "fixture handoff", "facts": ["fixture task and Git state were checked"],
            "evidence_paths": ["evidence.md"], "next_action": "continue the fixture task", "blockers": [], "risks": [],
            "validation": [{"command": "fixture check", "result": "passed"}],
            "rollout": {"path": str(rollout or self.make_rollout()), "session_id": "fixture-session"},
            "memory_projection": {"semantic_capsule": capsule, "local": [], "archive_refs": []},
        }, handle, ensure_ascii=False)
        handle.write("\n")
        handle.close()
        self.addCleanup(request.unlink, missing_ok=True)
        return request

    @staticmethod
    def handoff_path_from(stdout: str) -> str:
        return json.loads(stdout)["handoff_path"]

    @staticmethod
    def historical_payload(payload: dict, version: int) -> dict:
        payload = copy.deepcopy(payload)
        payload["schema_version"] = version
        conversation = payload["conversation"]
        for item in conversation["timeline"]:
            candidate = conversation["candidates"][item["event_index"] - 1]
            item.update(summary=candidate["text"], source=candidate["source"])
        payload["source"]["rollout"].update(coverage=conversation["coverage"], conversation_candidates=conversation["candidates"], timeline=conversation["timeline"])
        if version == 8:
            payload["memory_projection"]["legacy_extension"] = []
        return payload

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
        self.assertEqual(payload["schema_version"], 10)
        self.assertEqual(set(payload["source"]["rollout"]), {"path", "session_id", "capture_end", "record_count", "parser_version"})
        self.assertTrue(all("summary" not in item and "source" not in item for item in payload["conversation"]["timeline"]))
        self.assertNotIn("integrity", payload)
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

    def test_observation_preserves_distinct_proof_references(self) -> None:
        normalized = handoff.validate_observation({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "source-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "task": {"status": "completed", "completion_artifact": "task-proof"},
            "memory": {"status": "verified", "proof_ref": "memory-proof"},
        })
        self.assertEqual(normalized["boundary"]["proof_ref"], "boundary-proof")
        self.assertEqual(normalized["capsule"]["proof_ref"], "capsule-proof")
        self.assertEqual(normalized["memory"]["proof_ref"], "memory-proof")

    def test_consumed_conversation_fields_are_validated(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        core = root / relative
        original = json.loads(core.read_text())
        for conversation in ([], {}, {**original["conversation"], "candidates": []}):
            with self.subTest(conversation=type(conversation).__name__):
                payload = copy.deepcopy(original)
                payload["conversation"] = conversation
                core.write_text(json.dumps(payload))
                result = self.run_cli(root, "validate", "--handoff", relative)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["status"], "recovery_required")
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_consumed_shapes_fail_at_every_entry(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        core = root / relative
        original = json.loads(core.read_text())
        mutations = [
            (("conversation", "candidates"), {}),
            (("conversation", "candidates", 0, "event_index"), True),
            (("conversation", "candidates", 1, "event_index"), 1),
            (("conversation", "candidates", 0, "source", "byte_end"), original["source"]["rollout"]["capture_end"] + 1),
            (("conversation", "timeline", 0, "event_index"), 2),
            (("conversation", "timeline", 1, "supersedes_event_index"), 2),
            (("conversation", "timeline", 0, "repeat_count"), 0),
            (("conversation", "coverage", "event_count"), 0),
            (("conversation", "coverage", "event_count"), original["conversation"]["coverage"]["event_count"] + 1),
            (("conversation", "coverage", "unknown"), {"unknown": 1}),
            (("conversation", "coverage", "compacted_spans"), []),
            (("conversation", "coverage", "incomplete_tool_calls"), ["call-1"]),
            (("source", "git", "recent_commits"), [0]),
            (("project", "extra"), "unconsumed"),
            (("verified", "validation", 0), {"command": "missing result"}),
            (("memory_projection", "semantic_capsule"), ""),
            (("source", "rollout", "coverage"), original["conversation"]["coverage"]),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                payload = copy.deepcopy(original)
                target = payload
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                core.write_text(json.dumps(payload))
                for arguments in (("validate",), ("read", "--view", "core"), ("prepare",)):
                    result = self.run_cli(root, *arguments, "--handoff", relative)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)["status"], "recovery_required")
                    self.assertNotIn("Traceback", result.stderr)
                result = subprocess.run(["python3", str(SKILL / "scripts/render_handoff_prompt.py"), "--project-root", str(root), "--handoff", relative], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((root / handoff.LIFECYCLE_RUNTIME).exists())
        self.assertFalse(core.with_name("session-handoff-prompt.md").exists())

    def test_empty_capsule_is_rejected_without_creating_a_package(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        result = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule=" ")), "--explicit-user-request")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((root / handoff.HANDOFFS).exists())

    def test_views_page_long_unicode_without_writes_or_loss(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = root / "long.jsonl"
        message = "决定 `paging`：" + "汉字😀🧑‍💻 " * 2000
        rollout.write_text(json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": message}}, ensure_ascii=False) + "\n")
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout, capsule="合同😀 " * 1800)), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        core = root / relative
        before = core.read_bytes()
        payload = json.loads(before)
        for view, event_index in (("core", None), ("history", None), ("history", 1)):
            offset, pieces = 0, []
            while True:
                result = self.run_cli(root, "read", "--handoff", relative, "--view", view, "--offset", str(offset), "--length", "4096", *([] if event_index is None else ["--event-index", str(event_index)]))
                self.assertEqual(result.returncode, 0, result.stdout)
                page = json.loads(result.stdout)
                self.assertEqual(page["offset"], offset)
                self.assertEqual(page["next_offset"], offset + len(page["text"]))
                pieces.append(page["text"])
                offset = page["next_offset"]
                if page["complete"]:
                    break
            content = "".join(pieces)
            self.assertEqual(len(content), page["total_chars"])
            value = json.loads(content)
            if view == "core":
                self.assertNotIn("conversation", value)
                self.assertEqual({key: value[key] for key in payload if key != "conversation"}, {key: item for key, item in payload.items() if key != "conversation"})
                self.assertEqual(value["history_summary"]["candidate_count"], 1)
            elif event_index is None:
                self.assertEqual(value, payload["conversation"])
            else:
                self.assertEqual(value["text"], message.strip())
                self.assertEqual(value, payload["conversation"]["candidates"][0])
            end = handoff.read_view(root, relative, view, offset, 1, event_index)
            self.assertTrue(end["complete"])
            self.assertEqual(end["text"], "")
        for arguments in (("--offset", "-1"), ("--length", "0"), ("--offset", "99999999"), ("--event-index", "1")):
            self.assertEqual(self.run_cli(root, "read", "--handoff", relative, "--view", "core", *arguments).returncode, 2)
        for index in ("0", "2"):
            self.assertEqual(self.run_cli(root, "read", "--handoff", relative, "--view", "history", "--event-index", index).returncode, 2)
        self.assertEqual(core.read_bytes(), before)
        self.assertFalse((root / handoff.LIFECYCLE_RUNTIME).exists())

    def test_legal_coverage_exceptions_and_empty_history(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        with rollout.open("ab") as handle:
            for record in ({"type": "future_kind", "payload": {}}, {"type": "response_item", "payload": {"type": "future_item"}}, {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": []}}, {"type": "response_item", "payload": {"type": "function_call", "name": "tool", "call_id": "unmatched"}}):
                handle.write(json.dumps(record).encode() + b"\n")
            handle.write(b"\n" + b'{"type":"partial')
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout)
        relative = self.handoff_path_from(written.stdout)
        payload = json.loads((root / relative).read_text())
        coverage = payload["conversation"]["coverage"]
        self.assertEqual(coverage["unknown"], {"future_kind": 1, "response_item:future_item": 1})
        self.assertEqual(coverage["incomplete_tool_calls"], ["unmatched"])
        self.assertEqual(coverage["omissions"][-1]["kind"], "trailing_partial_record")
        self.assertEqual(self.run_cli(root, "validate", "--handoff", relative).returncode, 0)
        partial = payload["conversation"]["coverage"]["omissions"].pop()
        core = root / relative
        core.write_text(json.dumps(payload))
        self.assertEqual(self.run_cli(root, "validate", "--handoff", relative).returncode, 2)
        payload["conversation"]["coverage"]["omissions"].append(partial)
        core.write_text(json.dumps(payload))
        rollout.write_bytes(b"")
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(json.loads(handoff.read_view(root, relative, "history", 0, 4096)["text"])["candidates"], [])

    def test_history_attestation_ranges_are_checked_and_receipted(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        payload = json.loads((root / relative).read_text())
        size = handoff.read_view(root, relative, "history", 0, 1)["total_chars"]
        candidate_size = handoff.read_view(root, relative, "history", 0, 1, 1)["total_chars"]
        base = {"target_source": "session:target", "core_view_read": True, "prompt_read": True, "trellis_started": True, "facts_reconciled": True, "action_authorized": False, "task_disposition": "none", "task_path": None, "continuation_status": "absent", "history_read": "none", "history_refs": []}
        def check(value: dict) -> None:
            handoff._validate_history_reading(payload, handoff.validate_attestation(value))
        for change in ({"history_read": "partial"}, {"history_refs": [{"event_index": None, "offset": 0, "next_offset": 1}]}, {"history_read": "full", "history_refs": [{"event_index": 1, "offset": 0, "next_offset": candidate_size}]}, {"history_read": "full", "history_refs": [{"event_index": None, "offset": 1, "next_offset": size}]}, {"history_read": "partial", "history_refs": [{"event_index": True, "offset": 0, "next_offset": 1}]}, {"history_read": "partial", "history_refs": [{"event_index": 999, "offset": 0, "next_offset": 1}]}, {"history_read": "partial", "history_refs": [{"event_index": None, "offset": 0, "next_offset": size + 1}]}, {"history_read": "partial", "history_refs": [{"event_index": None, "offset": 1, "next_offset": 1}]}):
            with self.subTest(change=change), self.assertRaises(handoff.ContractError):
                check({**base, **change})
        old = {**base, "core_read": base["core_view_read"]}
        del old["core_view_read"]
        with self.assertRaises(handoff.ContractError):
            check(old)
        check(base)
        check({**base, "history_read": "partial", "history_refs": [{"event_index": 1, "offset": 0, "next_offset": candidate_size}]})
        full = {**base, "history_read": "full", "history_refs": [{"event_index": None, "offset": size // 2, "next_offset": size}, {"event_index": None, "offset": 0, "next_offset": size // 2}]}
        check(full)
        (root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n")
        handoff.lifecycle_prepare(root, relative, "core_only")
        handoff.lifecycle_seal(root, relative, explicit=True)
        attestation = root / "attestation.json"
        attestation.write_text(json.dumps(full))
        with mock.patch.dict(os.environ, {"FIXTURE_TARGET": "target"}):
            result = handoff.lifecycle_admit(root, relative, "attestation.json")
            self.assertEqual(result[1]["status"], "recorded")
            self.assertEqual(handoff.lifecycle_admit(root, relative, "attestation.json")[1]["status"], "idempotent")
        events = handoff._read_events(handoff._lifecycle_path(root, payload["handoff_id"]), payload["handoff_id"])
        self.assertIn("history_read=full", events[-1]["evidence_refs"])
        self.assertIn("history_refs=" + json.dumps(full["history_refs"], ensure_ascii=True, sort_keys=True, separators=(",", ":")), events[-1]["evidence_refs"])

    def test_core_only_mode_admits_after_boundary_is_sealed(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        (root / ".trellis/scripts/task.py").write_text(
            "import json, os\nprint(json.dumps({'current_task': None, 'source': 'none', 'session_source': 'session:' + os.environ.get('FIXTURE_TARGET', 'source')}))\n",
            encoding="utf-8",
        )
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule="verified semantic capsule")), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only").returncode, 0)
        package = root / Path(relative).parent
        (package / "session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        observation = root / ".trellis/.runtime/observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        proof = {
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "fixture-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "task": {"status": "completed", "completion_artifact": "task-proof"},
            "memory": {"status": "verified", "proof_ref": "memory-proof"},
        }
        observation.write_text(json.dumps(proof), encoding="utf-8")
        self.assertEqual(self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root))).returncode, 0)
        attestation = root / ".trellis/.runtime/attestation.json"
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        with mock.patch.dict(os.environ, {"FIXTURE_TARGET": "target"}):
            blocked = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(blocked[1]["status"], "recorded")
        self.assertEqual(blocked[1]["state"]["target"], "reconciled")
        self.assertEqual(blocked[1]["state"]["retention"], "archive_eligible")

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

    def test_semantic_capsule_and_post_compaction_reentry_are_preserved(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        capsule = "目标与已否决方案：" + ("语义现场 " * 5000)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule=capsule)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        self.assertEqual(payload["memory_projection"]["semantic_capsule"], capsule)
        (root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n", encoding="utf-8")
        prepared = self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only")
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        observation = root / ".trellis/.runtime/observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        observation.write_text(json.dumps({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "fixture-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "task": {"status": "incomplete", "completion_artifact": None},
            "memory": {"status": "unverified", "proof_ref": None},
        }), encoding="utf-8")
        self.assertEqual(self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root))).returncode, 0)

        attestation = root / ".trellis/.runtime/attestation.json"
        attestation.parent.mkdir(parents=True, exist_ok=True)
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        os.environ["FIXTURE_TARGET"] = "target"
        self.addCleanup(os.environ.pop, "FIXTURE_TARGET", None)
        admitted = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(admitted[1]["status"], "recorded")

        attestation.write_text(json.dumps({
            "target_source": "session:other", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        os.environ["FIXTURE_TARGET"] = "other"
        self.addCleanup(os.environ.pop, "FIXTURE_TARGET", None)
        with self.assertRaisesRegex(handoff.ContractError, "already been consumed"):
            handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))

        os.environ["FIXTURE_TARGET"] = "target"
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        repeated = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(repeated[1]["status"], "idempotent")
        events = handoff._read_events(handoff._lifecycle_path(root, Path(relative).parts[-2]), Path(relative).parts[-2])
        self.assertEqual(sum(event["event_type"] == "admit" and event["target_status"] == "reconciled" for event in events), 1)

    def test_new_core_has_no_snapshot_or_projection_limits(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        (root / ".trellis/tasks/demo/task.json").write_text(json.dumps({
            "id": "fixture-task", "status": "in_progress", "notes": "detail " * 20000,
        }), encoding="utf-8")
        rollout = root / "large-rollout.jsonl"
        rollout.write_text(
            "".join(
                json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "决定 `item-%d`" % index}}, ensure_ascii=False) + "\n"
                for index in range(600)
            ),
            encoding="utf-8",
        )
        request_path = self.make_request(root, rollout, capsule="现场 " * 5000)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["facts"] = ["fact-%d" % index for index in range(64)]
        request["validation"] = [{"command": "check-%d" % index, "result": "ok"} for index in range(24)]
        request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        written = self.run_cli(root, "write", "--request", str(request_path), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        self.assertEqual(payload["work_context"]["task"]["id"], "fixture-task")
        self.assertEqual(len(payload["conversation"]["candidates"]), 600)
        self.assertEqual(len(payload["verified"]["facts"]), 64)
        self.assertNotIn("integrity", payload)
        self.assertNotIn("sha256", json.dumps(payload))
        self.assertEqual(json.loads(self.run_cli(root, "validate", "--handoff", relative).stdout)["status"], "ready")
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only").returncode, 0)
        receipt = (root / handoff.LIFECYCLE_RUNTIME / (Path(relative).parts[-2] + ".jsonl")).read_text(encoding="utf-8")
        self.assertNotIn("digest", receipt)

    def test_legacy_schema_is_rejected(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule="verified semantic capsule")), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        core = root / relative
        payload = json.loads(core.read_text(encoding="utf-8"))
        payload["schema_version"] = 5
        payload["project"]["identity_digest"] = "sha256:legacy"
        payload["source"]["evidence"] = [{"path": "evidence.md", "bytes": 1, "sha256": "sha256:legacy"}]
        payload["source"]["rollout"].update({"device": 1, "inode": 2, "prefix_sha256": "sha256:legacy"})
        payload["integrity"] = {"payload_digest": "sha256:legacy", "source_digest": "sha256:legacy"}
        core.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        validated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertNotEqual(validated.returncode, 0)
        self.assertEqual(json.loads(validated.stdout)["status"], "recovery_required")

    def test_admit_requires_paired_assets_and_recovers_one_incomplete_intake(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        (root / ".trellis/scripts/task.py").write_text(
            "import json, os\nprint(json.dumps({'current_task': None, 'source': 'none', 'session_source': 'session:' + os.environ.get('FIXTURE_TARGET', 'source')}))\n",
            encoding="utf-8",
        )
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule="verified semantic capsule")), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only").returncode, 0)
        attestation = root / ".trellis/.runtime/attestation.json"
        attestation.parent.mkdir(parents=True, exist_ok=True)
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": False, "history_read": "none", "history_refs": [], "prompt_read": False,
            "trellis_started": False, "facts_reconciled": False, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        with self.assertRaisesRegex(handoff.ContractError, "paired handoff prompt"):
            handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        handoff_id = Path(relative).parts[-2]
        self.assertEqual(sum(event["target_status"] == "reconciled" for event in handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)), 0)

        (root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n", encoding="utf-8")
        observation = root / ".trellis/.runtime/observation.json"
        observation.write_text(json.dumps({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "fixture-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "task": {"status": "incomplete", "completion_artifact": None},
            "memory": {"status": "unverified", "proof_ref": None},
        }), encoding="utf-8")
        self.assertEqual(self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root))).returncode, 0)
        os.environ["FIXTURE_TARGET"] = "target"
        self.addCleanup(os.environ.pop, "FIXTURE_TARGET", None)
        incomplete = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(incomplete[1]["status"], "incomplete")
        self.assertEqual(incomplete[1]["state"]["target"], "not_admitted")
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": False,
            "trellis_started": False, "facts_reconciled": False, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        self.assertEqual(handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))[1]["status"], "incomplete")
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": False, "history_read": "none", "history_refs": [], "prompt_read": False,
            "trellis_started": False, "facts_reconciled": False, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        self.assertEqual(handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))[1]["status"], "incomplete")
        attestation.write_text(json.dumps({
            "target_source": "session:target", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        self.assertEqual(handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))[1]["status"], "recorded")
        self.assertEqual(sum(event["target_status"] == "reconciled" for event in handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)), 1)

    def test_finalize_requires_the_canonical_prompt_pair(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only").returncode, 0)
        observation = root / ".trellis/.runtime/observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        observation.write_text(json.dumps({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "fixture-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "task": {"status": "incomplete", "completion_artifact": None},
            "memory": {"status": "unverified", "proof_ref": None},
        }), encoding="utf-8")
        missing = self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root)))
        self.assertNotEqual(missing.returncode, 0)
        handoff_id = Path(relative).parts[-2]
        self.assertEqual([event["event_type"] for event in handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)], ["prepare"])

    def test_rollout_prefix_mutation_and_evidence_drift_are_reconciled_by_target(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        raw = rollout.read_bytes()
        rollout.write_bytes(b" " + raw[1:])
        mutated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(mutated.stdout)["status"], "ready")

        written = self.run_cli(root, "write", "--request", str(self.make_request(root, self.make_rollout())), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        (root / "evidence.md").write_text("changed\n", encoding="utf-8")
        drifted = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(drifted.stdout)["status"], "ready")

    def test_old_fixed_path_is_not_a_valid_package(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        result = self.run_cli(root, "validate", "--handoff", ".trellis/session-handoff.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timestamped handoff package", json.loads(result.stdout)["reason"])

    def test_lifecycle_archive_purge_restore_and_session_provenance(self) -> None:
        root = self.make_root()
        self.addCleanup(shutil.rmtree, root)
        (root / "evidence.md").write_text("verified fixture\n", encoding="utf-8")
        (root / ".trellis/scripts/task.py").write_text(
            "import json, os\nprint(json.dumps({'current_task': None, 'source': 'none', 'session_source': 'session:' + os.environ.get('FIXTURE_TARGET', 'source')}))\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        rollout = self.make_rollout()
        request = self.make_request(root, rollout)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        handoff_id = Path(relative).parts[-2]
        package = root / Path(relative).parent

        prepare = self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only")
        self.assertEqual(prepare.returncode, 0, prepare.stderr)
        self.assertEqual(json.loads(prepare.stdout)["status"], "recorded")
        repeated = self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(json.loads(repeated.stdout)["status"], "idempotent")

        observation = package / "observation.json"
        observation.write_text(json.dumps({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "local-boundary"},
            "source_session": {"status": "verified", "identity": "source-session"},
            "capsule": {"status": "verified", "proof_ref": "local-capsule"},
            "task": {"status": "completed", "completion_artifact": "task-complete"},
            "memory": {"status": "verified", "proof_ref": "local-memory"},
        }), encoding="utf-8")
        (package / "session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        finalized = self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root)))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        self.assertEqual(json.loads(finalized.stdout)["status"], "recorded")
        attestation = package / "attestation.json"
        attestation.write_text(json.dumps({
            "target_source": "session:target-session", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        (package / "session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        os.environ["FIXTURE_TARGET"] = "target-session"
        self.addCleanup(os.environ.pop, "FIXTURE_TARGET", None)
        admitted = self.run_cli(root, "admit", "--handoff", relative, "--attestation", str(attestation.relative_to(root)))
        self.assertEqual(admitted.returncode, 0, admitted.stderr)
        self.assertEqual(json.loads(admitted.stdout)["status"], "recorded")
        prompt = package / "session-handoff-prompt.md"

        prompt.unlink()
        missing_canonical_prompt = self.run_cli(root, "retention", "archive", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertNotEqual(missing_canonical_prompt.returncode, 0)
        self.assertEqual(json.loads(self.run_cli(root, "status", "--handoff", relative).stdout)["state"]["retention"], "archive_eligible")
        archive = root / handoff.ARCHIVE_RUNTIME / handoff_id
        self.assertFalse(archive.exists())
        prompt.write_text("handoff prompt\n", encoding="utf-8")

        archived = self.run_cli(root, "retention", "archive", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(archived.returncode, 0, archived.stderr)
        self.assertEqual({path.name for path in archive.iterdir()}, {"session-handoff.json", "session-handoff-prompt.md"})
        repeated_archive = self.run_cli(root, "retention", "archive", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(repeated_archive.returncode, 0, repeated_archive.stderr)
        self.assertEqual(json.loads(repeated_archive.stdout)["status"], "idempotent")

        core = root / relative
        purged = self.run_cli(root, "retention", "purge", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(purged.returncode, 0, purged.stderr)
        self.assertFalse(core.exists())
        self.assertFalse(prompt.exists())
        self.assertTrue((root / "evidence.md").exists())

        archived_prompt = archive / "session-handoff-prompt.md"
        archived_prompt.unlink()
        events_before = handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)
        incomplete_status = self.run_cli(root, "status", "--handoff", relative)
        self.assertNotEqual(incomplete_status.returncode, 0)
        incomplete_restore = self.run_cli(root, "retention", "restore", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertNotEqual(incomplete_restore.returncode, 0)
        self.assertEqual(handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id), events_before)
        archived_prompt.write_text("handoff prompt\n", encoding="utf-8")

        restored = self.run_cli(root, "retention", "restore", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertTrue(core.is_file())
        self.assertTrue(prompt.is_file())
        status = self.run_cli(root, "status", "--handoff", relative)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["status"], "ready")
        reopened = self.run_cli(root, "retention", "reopen", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(reopened.returncode, 0, reopened.stderr)

    def test_lifecycle_rejects_source_session_reuse_and_serializes_idempotence(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        request = self.make_request(root, rollout)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: handoff.lifecycle_prepare(root, relative, "core_only"), range(2)))
        self.assertEqual({result[1]["status"] for result in results}, {"recorded", "idempotent"})
        handoff_id = Path(relative).parts[-2]
        (root / relative).with_name("session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        attestation = root / ".trellis/.runtime" / "attestation.json"
        attestation.parent.mkdir(parents=True, exist_ok=True)
        attestation.write_text(json.dumps({
            "target_source": "session:fixture-session", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        with self.assertRaisesRegex(handoff.ContractError, "source session id"):
            handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertTrue(handoff_id)

    def test_receipt_lock_allows_only_one_reconciled_admit_target(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        handoff_id, _, _ = handoff._core(root, relative)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only").returncode, 0)

        desired = {"source": "prepared", "target": "reconciled", "retention": "archive_eligible"}

        def admit(target: str) -> str:
            try:
                return handoff._append_event(
                    root, handoff_id, "admit", desired, ["target=session:" + target],
                )["status"]
            except handoff.ContractError:
                return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(admit, ["target-a", "target-b"]))

        self.assertEqual(sorted(outcomes), ["recorded", "rejected"])
        events = handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)
        self.assertEqual(sum(event["event_type"] == "admit" and event["target_status"] == "reconciled" for event in events), 1)

    def test_taskless_local_seal_rejects_same_source(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule="capsule")), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        handoff.lifecycle_prepare(root, relative, "core_only")
        (root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n")
        with self.assertRaisesRegex(handoff.ContractError, "explicit-user-request"):
            handoff.lifecycle_seal(root, relative, explicit=False)
        handoff.lifecycle_seal(root, relative, explicit=True)
        self.assertEqual(handoff.lifecycle_status(root, relative)["status"], "ready")
        attestation = root / "attestation.json"
        payload = {"target_source": "session:source", "core_view_read": True, "history_read": "none", "history_refs": [], "prompt_read": True, "trellis_started": True, "facts_reconciled": True, "action_authorized": False, "task_disposition": "none", "task_path": None, "continuation_status": "absent"}
        attestation.write_text(json.dumps(payload))
        with self.assertRaisesRegex(handoff.ContractError, "prepared source session"):
            handoff.lifecycle_admit(root, relative, "attestation.json")
        with mock.patch.dict(os.environ, {"FIXTURE_TARGET": "target"}):
            payload["target_source"] = "session:target"
            attestation.write_text(json.dumps(payload))
            self.assertEqual(handoff.lifecycle_admit(root, relative, "attestation.json")[1]["status"], "recorded")

    def test_schema_8_and_9_are_read_only_and_never_use_old_read_semantics(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        core = root / relative
        current = json.loads(core.read_text())
        observation = root / ".trellis/.runtime/observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        observation.write_text(json.dumps({
            "availability": "available", "boundary": {"status": "sealed", "proof_ref": "boundary"},
            "source_session": {"status": "verified", "identity": "source"},
            "capsule": {"status": "verified", "proof_ref": "capsule"},
            "task": {"status": "incomplete", "completion_artifact": None},
            "memory": {"status": "unverified", "proof_ref": None},
        }))
        for version in (8, 9):
            with self.subTest(version=version):
                payload = self.historical_payload(current, version)
                core.write_text(json.dumps(payload))
                receipt = handoff._lifecycle_path(root, payload["handoff_id"])
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text("opaque historical lifecycle receipt\n")
                before = (core.read_bytes(), receipt.read_bytes())
                self.assertEqual(handoff.validate(root, payload, payload["handoff_id"]), "historical")
                self.assertEqual(json.loads(self.run_cli(root, "validate", "--handoff", relative).stdout)["status"], "historical")
                self.assertEqual(self.run_cli(root, "read", "--handoff", relative, "--view", "core").returncode, 2)
                historical_status = handoff.lifecycle_status(root, relative)
                self.assertEqual(historical_status["status"], "historical")
                self.assertIsNone(historical_status["mode"])
                archive = root / handoff.ARCHIVE_RUNTIME / payload["handoff_id"]
                archive.mkdir(parents=True, exist_ok=True)
                (archive / handoff.HANDOFF_NAME).write_bytes(core.read_bytes())
                (archive / "session-handoff-prompt.md").write_text("historical prompt\n")
                operations = {
                    "prepare": ["prepare"],
                    "finalize": ["finalize", "--observation", str(observation.relative_to(root))],
                    "seal": ["seal", "--explicit-user-request"],
                    "admit": ["admit", "--attestation", "missing.json"],
                    "retention": ["retention", "archive", "--confirm-handoff-id", payload["handoff_id"]],
                    "restore": ["retention", "restore", "--confirm-handoff-id", payload["handoff_id"]],
                    "reopen": ["retention", "reopen", "--confirm-handoff-id", payload["handoff_id"]],
                    "purge": ["retention", "purge", "--confirm-handoff-id", payload["handoff_id"]],
                    "ownership_quiesce": ["ownership", "quiesce", "--explicit-user-request"],
                    "ownership_claim": ["ownership", "claim", "--expected-generation", "0", "--explicit-user-request"],
                }
                for label, args in operations.items():
                    result = self.run_cli(root, *args, "--handoff", relative)
                    self.assertEqual(result.returncode, 2, label)
                    self.assertIn("read-only", result.stdout)
                self.assertEqual(self.run_cli(root, "ownership", "status", "--handoff", relative).returncode, 0)
                self.assertEqual((core.read_bytes(), receipt.read_bytes()), before)
                shutil.rmtree(archive)

    def test_invalid_current_is_not_a_taskless_snapshot(self) -> None:
        root = self.make_root()
        self.addCleanup(shutil.rmtree, root)
        for extra in ({"error": {"reason": "invalid"}}, {"stale": True}, {"source": "unbound_ambiguous"}, {"candidates": ["one"]}):
            value = {"current_task": None, "source": "none", "session_source": "session:source", **extra}
            (root / ".trellis/scripts/task.py").write_text("import json\nprint(" + repr(json.dumps(value)) + ")\n")
            with self.assertRaises(handoff.ContractError):
                handoff._task_snapshot(root)

    def test_ownership_adapter_keeps_core_immutable_and_records_distinct_receipts(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        task_script = root / ".trellis/scripts/task.py"
        task_script.write_text(
            "import json, os, sys\n"
            "args = sys.argv[1:]\n"
            "target = os.environ.get('TRELLIS_CONTEXT_ID') == 'target'\n"
            "task = None if target else {'id': 'fixture-task', 'dir': '.trellis/tasks/demo', 'status': 'in_progress'}\n"
            "if args == ['current', '--json']:\n"
            "    print(json.dumps({'current_task': task, 'source': 'session:' + ('target' if target else 'source'), 'session_source': 'session:' + ('target' if target else 'source')}))\n"
            "elif args and args[0] == 'ownership':\n"
            "    op = args[1]\n"
            "    with open('.trellis/.runtime/ownership-args.jsonl', 'a', encoding='utf-8') as handle:\n"
            "        handle.write(json.dumps(args) + '\\n')\n"
            "    if op == 'status':\n"
            "        print(json.dumps({'status': 'ready', 'generation': 3, 'record_digest': 'sha256:' + 'a' * 64}))\n"
            "        raise SystemExit(0)\n"
            "    generations = {'quiesce': 0, 'seal': 1, 'retire': 3, 'retire-handoff': 3, 'claim': 5, 'consume': 6, 'archive': 7}\n"
            "    statuses = {'quiesce': 'quiescing', 'seal': 'sealed', 'retire': 'ready', 'retire-handoff': 'ready', 'claim': 'claimed', 'consume': 'consumed', 'archive': 'archived'}\n"
            "    print(json.dumps({'status': statuses[op], 'generation': generations.get(op, 5), 'record_digest': 'sha256:' + 'a' * 64}))\n"
            "else:\n"
            "    raise SystemExit(2)\n",
            encoding="utf-8",
        )
        rollout = self.make_rollout()
        request = self.make_request(root, rollout)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        before = (root / relative).read_bytes()
        handoff_id = Path(relative).parts[-2]

        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only").returncode, 0)
        package = root / Path(relative).parent
        (package / "session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        observation = root / ".trellis/.runtime/observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        observation.write_text(json.dumps({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "fixture-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "task": {"status": "incomplete", "completion_artifact": None},
            "memory": {"status": "unverified", "proof_ref": None},
        }), encoding="utf-8")
        self.assertEqual(self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root))).returncode, 0)
        self.assertNotEqual(self.run_cli(root, "status", "--handoff", relative).returncode, 0)
        self.assertEqual(handoff.ownership_operation(root, "quiesce", relative, explicit=True)["ownership"]["status"], "quiescing")
        self.assertEqual(handoff.ownership_operation(root, "seal", relative, explicit=True, expected_generation=0)["ownership"]["status"], "sealed")
        self.assertEqual(self.run_cli(root, "status", "--handoff", relative).returncode, 0)
        self.assertEqual(handoff.ownership_operation(root, "retire-handoff", relative, explicit=True)["ownership"]["generation"], 3)

        os.environ["TRELLIS_CONTEXT_ID"] = "target"
        self.addCleanup(os.environ.pop, "TRELLIS_CONTEXT_ID", None)
        claimed = handoff.ownership_operation(root, "claim", relative, explicit=True, expected_generation=3)
        repeated = handoff.ownership_operation(root, "claim", relative, explicit=True, expected_generation=3)
        self.assertEqual(claimed["ownership"]["status"], "claimed")
        self.assertEqual(repeated["lifecycle"]["status"], "idempotent")
        self.assertEqual(handoff.ownership_operation(root, "consume", relative, explicit=True, expected_generation=5)["ownership"]["status"], "consumed")
        self.assertEqual(handoff.ownership_operation(root, "archive", relative, explicit=True, expected_generation=6)["ownership"]["status"], "archived")
        self.assertEqual(handoff.ownership_operation(root, "status", relative, explicit=False)["ownership"]["status"], "ready")
        self.assertEqual((root / relative).read_bytes(), before)
        events = (root / handoff.LIFECYCLE_RUNTIME / (handoff_id + ".jsonl")).read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum('"event_type": "ownership_claim"' in line for line in events), 1)


if __name__ == "__main__":
    unittest.main()
