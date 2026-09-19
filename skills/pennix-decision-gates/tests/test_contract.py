from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class DecisionGatesContractTests(unittest.TestCase):
    def test_frontier_round_contract_is_present(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in ("## Frontier And Rounds", "calculate the frontier", "recalculates the"):
            self.assertIn(marker, content)

    def test_gate_keeps_trellis_brainstorm_boundary(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("ordinary one-question `trellis-brainstorm` flow", content)
        self.assertIn("does not create a", content)


if __name__ == "__main__":
    unittest.main()
