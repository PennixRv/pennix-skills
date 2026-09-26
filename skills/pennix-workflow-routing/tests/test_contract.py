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

    def test_trellis_parallel_route_preserves_native_admission_and_acceptance(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        route = content.split("## 当前 Trellis fork 并行工作流", 1)[1].split("## 本地证据优先", 1)[0]
        for invariant in (
            "主会话 inline 完成",
            "按决策复杂度调用 `$pennix-decision-gates`",
            "`subnode-work` procedure",
            "`.trellis/agents/subnode-profiles.json`",
            "动态解析模型与 reasoning effort",
            "一个原生终态 wait",
            "协调者核验报告完整性",
            "不得由 FastCtx 包装",
        ):
            self.assertIn(invariant, route)


if __name__ == "__main__":
    unittest.main()
