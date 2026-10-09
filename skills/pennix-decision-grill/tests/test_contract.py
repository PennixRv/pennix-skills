from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class DecisionGrillContractTests(unittest.TestCase):
    def test_frontier_round_contract_is_present(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in ("## Decision Chain State", "## Frontier And Rounds", "calculate the frontier", "conflict audit", "final seal"):
            self.assertIn(marker, content)

    def test_gate_keeps_trellis_brainstorm_boundary(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("does not create a second task lifecycle", content)

    def test_implementation_ambiguity_returns_through_replan(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("run `task.py replan <task>", content)
        self.assertIn("Never edit `task.json.status` by hand", content)

    def test_bounded_in_progress_amendment_keeps_current_lifecycle(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("Bounded user-requested amendments while in progress", content)
        self.assertIn("The explicit request authorizes only that exact bounded addition", content)
        self.assertIn("do not create a second lifecycle", content)
        self.assertIn("If any condition is false or unclear", content)
        self.assertIn("credentials, external data, public behavior", content)

    def test_research_does_not_require_implementation_approval(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("do not require implementation", content)
        self.assertIn("does not need a final seal or implementation approval", content)
        self.assertIn("frozen dispatch-plan gate", content)
        self.assertIn("only the named\nevidence", content)

    def test_request_is_classified_before_gate_selection(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("The caller must classify the request before entering this Skill", content)
        for marker in ("`work_domain`", "`delivery_mode`", "`execution_class`", "`decision_frontier`", "`approval_mode`"):
            self.assertIn(marker, content)
        self.assertIn("an unresolved user-owned choice may materially change", content)
        self.assertIn("A frontier may contain one decision", content)

    def test_same_continuation_answers_continue_after_persistence(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("Continue the\nsame planning flow", content)
        self.assertNotIn("After asking, stop the turn.", content)

    def test_final_seal_has_no_static_pending_decisions(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("no `TBD`, `TODO`, `decision-needed`", content)
        self.assertIn("completion\ncondition determined", content)


if __name__ == "__main__":
    unittest.main()
