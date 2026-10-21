import json
from pathlib import Path
import tempfile
import unittest

import run_codex_cases as runner


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
                 "../pennix-context-mode-integration/SKILL.md"]
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
