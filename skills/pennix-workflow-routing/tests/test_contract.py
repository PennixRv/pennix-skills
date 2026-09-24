from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class WorkflowRoutingContractTest(unittest.TestCase):
    def test_admission_precedes_route_selection(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "## Admission first",
            "`work_domain`",
            "`delivery_mode`",
            "`execution_class`",
            "`decision_frontier`",
            "`approval_mode`",
            "`analysis_only` 只表示",
            "`subnode` 只表示",
            "只有升级后的\ndecision frontier 需要 `$pennix-decision-gates`",
            "Admission 不是第二套状态机",
        ):
            self.assertIn(marker, content)

    def test_owner_first_rule_covers_workflow_native_protocols(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("直接调用唯一原生 owner", content)
        self.assertIn("原生不可用即停止", content)
        self.assertIn("专用 owner 不可用时不允许降级到 FastCtx", content)

    def test_grok_remains_an_external_retrieval_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`grok-search` 是外部检索 owner", content)
        self.assertIn("不能把它的网络调用", content)

    def test_project_trellis_updates_have_a_native_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`$pennix-trellis-project-update` 负责", content)
        self.assertIn("原生 `trellis update` / `trellis workflow`", content)
        self.assertIn("`workflow-doctor` 只做只读诊断", content)

    def test_owner_transport_and_fastctx_default_are_both_explicit(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("先做 work-domain 和 native-owner preflight", content)
        self.assertIn("普通本地文件、非交互 CLI", content)
        self.assertIn("不得使用 `mcp__fastctx.run`", content)
        self.assertIn("正确 native channel 不可用时保留原始能力缺口并停止", content)
        self.assertIn("FastCtx 才能做不推进 owner 状态的读取或分析", content)


if __name__ == "__main__":
    unittest.main()
