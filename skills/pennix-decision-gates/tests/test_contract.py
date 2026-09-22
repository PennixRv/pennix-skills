from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class DecisionGatesContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
