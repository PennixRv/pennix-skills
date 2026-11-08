import json
from pathlib import Path
import tempfile
import unittest

import run_codex_cases as runner
import app_server_cases


class EvaluationDriverTests(unittest.TestCase):
    def summarize_items(self, *items):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text("\n".join(json.dumps({"type": "item.completed", "item": item})
                                      for item in items))
            return runner.summarize(path, "completed")

    def test_first_failure_survives_a_successful_retry(self):
        wrong = "/home/test/.codex/skills/pennix-grok-search/SKILL.md"
        correct = "/home/test/.codex/skills/pennix-skills/pennix-grok-search/SKILL.md"
        summary = self.summarize_items(
            {"type": "command_execution", "command": f"cat {wrong}", "exit_code": 1,
             "aggregated_output": "No such file"},
            {"type": "command_execution", "command": f"cat {correct}", "exit_code": 0,
             "aggregated_output": "---\nname: pennix-grok-search\n---\n# Search"},
        )
        observations = summary["skill_path_observations"]
        self.assertEqual([wrong, correct], [x["path"] for x in observations])
        self.assertEqual(["failed", "read"], [x["outcome"] for x in observations])
        self.assertLess(observations[0]["event"], observations[1]["event"])
        self.assertEqual(["pennix-grok-search"], summary["skill_read_candidates"])
        self.assertEqual({"read": 1, "failed": 1, "unknown": 0}, summary["skill_read_counts"])

    def test_failed_read_is_a_candidate_without_a_success(self):
        summary = self.summarize_items({
            "type": "command_execution", "command": "cat ../missing-skill/SKILL.md",
            "exit_code": 1, "aggregated_output": "No such file",
        })
        self.assertEqual(["missing-skill"], summary["skill_read_candidates"])
        self.assertEqual({"read": 0, "failed": 1, "unknown": 0}, summary["skill_read_counts"])

    def test_project_extra_expanded_alias_and_relative_paths_keep_all_levels(self):
        paths = [".agents/skills/trellis-before-dev/SKILL.md",
                 "/home/test/.codex/skills/pennix-skills-extra/diagnosing-bugs/SKILL.md",
                 "/declared/r0/pennix-skills/pennix-grok-search/SKILL.md",
                 "../pennix-workflow-routing/SKILL.md"]
        for path in paths:
            with self.subTest(path=path):
                summary = self.summarize_items({
                    "type": "command_execution", "command": f"/bin/zsh -lc 'cat {path}'",
                    "exit_code": 0, "aggregated_output": "# Skill content\n"})
                observation, = summary["skill_path_observations"]
                self.assertEqual(path, observation["path"])
                self.assertEqual(Path(path).parent.name, observation["skill"])
                self.assertEqual("read", observation["outcome"])

    def test_mentions_compound_commands_and_missing_output_stay_unknown(self):
        path = "/tmp/skills/pennix-routing/SKILL.md"
        items = [
            {"type": "command_execution", "command": f"echo {path}", "exit_code": 0,
             "aggregated_output": path},
            {"type": "command_execution", "command": f"cat {path}; true", "exit_code": 0,
             "aggregated_output": "No such file"},
            {"type": "command_execution", "command": f"cat {path}", "exit_code": 0},
            {"type": "command_execution", "command": f"cat {path}", "exit_code": None,
             "aggregated_output": "partial output"},
            {"type": "command_execution", "command": f"cat {path}", "exit_code": 0,
             "aggregated_output": {"invalid": "output"}},
            {"type": "mcp_tool_call", "server": "context-mode", "tool": "ctx_execute",
             "arguments": {"code": f"read({path})"}, "status": "completed"},
        ]
        summary = self.summarize_items(*items)
        self.assertEqual(["unknown"] * len(items),
                         [x["outcome"] for x in summary["skill_path_observations"]])
        self.assertEqual([path] * len(items),
                         [x["path"] for x in summary["skill_path_observations"]])
        self.assertEqual({"read": 0, "failed": 0, "unknown": len(items)}, summary["skill_read_counts"])

    def test_frozen_coverage_and_name_mapping(self):
        data, digest = runner.load_cases()
        self.assertEqual(64, len(digest))
        self.assertEqual(36, sum(x["kind"] not in {"combination", "interaction"} for x in data["cases"]))
        self.assertEqual(10, sum(x["kind"] == "combination" for x in data["cases"]))
        self.assertEqual(8, sum(x["kind"] == "interaction" for x in data["cases"]))
        self.assertTrue(all(name.startswith("pennix-") for x in data["cases"] for name in x["skills_after"]))

    def test_sources_bind_actual_tree_to_owner_receipt_and_fixed_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home / "skills/pennix-skills"
            root.mkdir(parents=True)
            member = root / "SKILL.md"
            member.write_bytes(b"source fixture\n")
            digest = runner.hashlib.sha256(b"F\0SKILL.md\0" + b"0\0source fixture\n").hexdigest()
            revision = "a" * 40
            receipt = root.parent / ".pennix-skills.receipt.json"
            value = {"schema": 1, "destination": root.name, "digest": digest,
                     "source": {"repo": "PennixRv/pennix-skills", "ref": revision, "manifest": "collection.json"},
                     "manifest": {"skills": {}}}
            receipt.write_text(json.dumps(value))
            identity = runner.source_identity(home, revision)
            self.assertEqual(revision, identity["collection_commit"])
            with self.assertRaisesRegex(ValueError, "source_mismatch"):
                runner.source_identity(home, "b" * 40)
            member.write_text("changed")
            with self.assertRaisesRegex(ValueError, "source_drift"):
                runner.source_identity(home, revision)
            member.unlink()
            member.symlink_to(receipt)
            with self.assertRaisesRegex(ValueError, "unsafe_evaluation_source"):
                runner.source_identity(home, revision)

    def test_budget_cannot_reset_or_silently_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(1, runner.reserve_turn(root, "fixture", "before", "S01-positive"))
            self.assertIsNone(runner.reserve_turn(root, "fixture", "before", "S01-positive"))
            with self.assertRaisesRegex(ValueError, "fixture_mismatch"):
                runner.reserve_turn(root, "changed", "before", "S02-positive")
            for _ in range(99):
                runner.reserve_turn(root, "fixture", "after", "C01", retry=True)
            with self.assertRaisesRegex(ValueError, "budget_exhausted"):
                runner.reserve_turn(root, "fixture", "after", "C01", retry=True)

    def test_raw_text_and_commands_do_not_enter_summary(self):
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "synthetic-secret"}},
            {"type": "item.completed", "item": {"type": "command_execution", "command": "cat /tmp/skills/pennix-grill/SKILL.md synthetic-secret", "exit_code": 0}},
            {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "context-mode", "tool": "ctx_search", "arguments": {"queries": ["synthetic-secret"]}, "status": "completed"}},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 3}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in events))
            summary = runner.summarize(path, "completed")
        self.assertNotIn("synthetic-secret", json.dumps(summary))
        self.assertEqual(["pennix-grill"], summary["skill_read_candidates"])
        self.assertEqual("review_needed", summary["verdict"])
        self.assertEqual(2, len(summary["tool_actions"]))

    def test_invalid_event_and_native_failure_are_not_passed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text("not json\n")
            self.assertEqual("blocked_invalid_event", runner.summarize(path, "completed")["verdict"])
            self.assertEqual("blocked_native_execution", runner.summarize(path, "native_failure")["verdict"])

    def test_command_keeps_model_and_trust_configuration(self):
        argv = runner.command(Path("/tmp/fixture"))
        self.assertIn("read-only", argv)
        self.assertNotIn("--ephemeral", argv)
        self.assertNotIn("--model", argv)
        self.assertNotIn("--ignore-user-config", argv)
        self.assertFalse(any("bypass" in part for part in argv))

    def test_native_question_response_uses_question_ids_and_rejects_secrets(self):
        message = {"id": "native-7", "params": {"isBlocking": True,
                   "questions": [{"id": "preference", "question": "Which order?"}]}}
        response = app_server_cases.answer_request(message, "demo first")
        self.assertEqual({"id": "native-7", "result": {"answers": {
            "preference": {"answers": ["demo first"]}}}}, response)
        message["params"]["questions"][0]["isSecret"] = True
        with self.assertRaisesRegex(ValueError, "unsafe_native_question"):
            app_server_cases.answer_request(message, "not a secret")

    def test_native_question_observations_do_not_infer_tool_name_from_host_flag(self):
        events = [
            {"method": "item/tool/requestUserInput", "params": {"isBlocking": True}},
            {"method": "evaluation/questionAnswered", "params": {}},
            {"method": "item/tool/requestUserInput", "params": {"isBlocking": False}},
            {"method": "evaluation/questionTools", "params": {
                "request_user_input": 2, "request_user_input_async": 0}},
            {"method": "turn/completed", "params": {"turn": {"status": "failed"}}},
            {"method": "item/completed", "params": {"item": {"type": "contextCompaction"}}},
        ]
        result = app_server_cases.observe(events)
        self.assertEqual(1, result["host_blocking_requests"])
        self.assertEqual(1, result["host_nonblocking_requests"])
        self.assertEqual(2, result["question_tool_calls"]["request_user_input"])
        self.assertEqual(0, result["question_tool_calls"]["request_user_input_async"])
        self.assertEqual(1, result["question_answers"])
        self.assertTrue(result["turn_failed"])
        self.assertTrue(result["compaction_observed"])

    def test_rollout_question_counts_bind_path_identity_and_current_turn(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "sessions").mkdir()
            path = home / "sessions/rollout.jsonl"
            events = [
                {"type": "session_meta", "payload": {"id": "thread-1"}},
                {"type": "turn_context", "payload": {"turn_id": "old"}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "request_user_input_async"}},
                {"type": "turn_context", "payload": {"turn_id": "new"}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "request_user_input"}},
            ]
            path.write_text("\n".join(json.dumps(event) for event in events))
            self.assertEqual({"request_user_input": 1, "request_user_input_async": 0},
                             app_server_cases.question_tools(path, home, "thread-1", "new"))
            with self.assertRaisesRegex(ValueError, "rollout_identity_mismatch"):
                app_server_cases.question_tools(path, home, "other", "new")
            outside = home / "outside.jsonl"
            outside.write_text(path.read_text())
            with self.assertRaisesRegex(ValueError, "unsafe_rollout_path"):
                app_server_cases.question_tools(outside, home, "thread-1", "new")

    def test_native_client_preserves_server_errors_and_rejects_unexpected_requests(self):
        import queue
        import time
        app = object.__new__(app_server_cases.AppServer)
        app.sequence, app.events, app.messages = 0, [], queue.Queue()
        sent = []
        app.send = sent.append
        app.messages.put({"id": 1, "error": {"code": -32602, "message": "invalid params"}})
        with self.assertRaisesRegex(ValueError, "native_rpc_error"):
            app.rpc("thread/start", {})
        self.assertEqual("thread/start", sent[0]["method"])
        app.messages.put({"id": "approval-1", "method": "item/commandExecution/requestApproval"})
        with self.assertRaisesRegex(ValueError, "unexpected_server_request"):
            app.rpc("thread/start", {})
        with self.assertRaises(TimeoutError):
            app.next(time.monotonic() - 1)


if __name__ == "__main__":
    unittest.main()
