import json
from pathlib import Path
import tempfile
import unittest

import run_codex_cases as runner


class EvaluationDriverTests(unittest.TestCase):
    def test_frozen_coverage_and_name_mapping(self):
        data, digest = runner.load_cases()
        self.assertEqual(64, len(digest))
        self.assertEqual(36, sum(x["kind"] != "combination" for x in data["cases"]))
        self.assertEqual(8, sum(x["kind"] == "combination" for x in data["cases"]))
        self.assertTrue(all(name.startswith("pennix-") for x in data["cases"] for name in x["skills_after"]))

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
        self.assertIn("--ephemeral", argv)
        self.assertNotIn("--model", argv)
        self.assertNotIn("--ignore-user-config", argv)
        self.assertFalse(any("bypass" in part for part in argv))


if __name__ == "__main__":
    unittest.main()
