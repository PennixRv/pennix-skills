from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class WorkflowRoutingContractTest(unittest.TestCase):
    def test_owner_first_rule_covers_workflow_native_protocols(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("直接调用唯一原生 owner", content)
        self.assertIn("原生不可用即停止", content)
        self.assertIn("专用 owner 不可用时不允许降级到 FastCtx", content)

    def test_grok_remains_an_external_retrieval_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`grok-search` 是外部检索 owner", content)
        self.assertIn("不能把它的网络调用", content)


if __name__ == "__main__":
    unittest.main()
