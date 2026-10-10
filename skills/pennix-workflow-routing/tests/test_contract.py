from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class WorkflowRoutingContractTest(unittest.TestCase):
    def test_admission_precedes_route_selection(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "## 调用前判定",
            "`work_domain`",
            "`delivery_mode`",
            "`execution_class`",
            "`decision_frontier`",
            "`approval_mode`",
            "`analysis_only` 表示受保护目标不变的只读证据交付",
            "明确研究请求授权主会话完成证据工作",
            "并行子节点先冻结派发方案并获明确批准",
            "这不是第二套状态机",
        ):
            self.assertIn(marker, content)

    def test_owner_first_rule_covers_workflow_native_protocols(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("对应组件或宿主规定的原生接口", content)
        self.assertIn("原生不可用时停止", content)
        self.assertIn("组件规定接口不可用时不允许用 FastCtx", content)

    def test_grok_remains_an_external_retrieval_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`grok-search` 负责外部检索", content)
        self.assertIn("不接管其网络调用", content)

    def test_project_trellis_updates_have_a_native_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`$pennix-trellis-project-update` 负责", content)
        self.assertIn("原生 `trellis update` / `trellis workflow`", content)
        self.assertIn("`workflow-doctor` 只做只读诊断", content)

    def test_owner_transport_and_fastctx_default_are_both_explicit(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("先判断请求和交付范围，再选择工具", content)
        self.assertIn("普通本地文件、非交互命令", content)
        self.assertIn("不能通过 FastCtx `run`", content)
        self.assertIn("若基础工具按正确原生调用仍不可用，保留原错误并停止", content)
        self.assertIn("FastCtx 可以读取或分析该文件，但不能确认或模拟组件状态", content)

    def test_fastctx_availability_uses_the_host_registry_not_nested_exec_tools(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`functions.exec` 的 `ALL_TOOLS` 不是宿主完整工具清单", content)
        self.assertIn("参数校验、权限、传输或服务错误", content)

    def test_trellis_parallel_route_preserves_native_admission_and_acceptance(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        route = content.split("## 当前 Trellis fork 并行工作流", 1)[1].split("## 本地证据优先", 1)[0]
        for invariant in (
            "默认由主会话完成",
            "`change_bearing` 工作需要原生规划封口与实施批准",
            "仅对会实质改变研究范围或方法的用户选择调用 `$pennix-decision-grill`",
            "首次 spawn/send 前",
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
