from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class FastCtxRoutingContractTest(unittest.TestCase):
    def test_native_workflow_protocols_are_excluded_before_fastctx(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "Trellis task",
            "正式 handoff",
            "`request_user_input`",
            "Hook",
            "owner\ncontrolled TUI",
            "必须直接调用其原生接口",
            "绝不以 `run`",
        ):
            self.assertIn(marker, content)

    def test_external_retrieval_owners_are_not_fastctx_adapters(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`grok-search`", content)
        self.assertIn("不调用、代替或吸收其检索协议", content)


if __name__ == "__main__":
    unittest.main()
