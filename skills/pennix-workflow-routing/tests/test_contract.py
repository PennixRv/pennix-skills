from pathlib import Path
import re
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
        self.assertIn("使用 owner 的真实命令和接口", content)
        self.assertIn("对应宿主或组件原生入口", content)
        self.assertIn("若基础工具按正确原生调用仍不可用", content)

    def test_grok_remains_an_external_retrieval_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`$pennix-grok-search` 负责外部检索", content)
        self.assertIn("不接管其网络调用", content)

    def test_project_trellis_updates_have_a_native_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`$pennix-trellis-project-update` 负责", content)
        self.assertIn("原生 `trellis update` / `trellis workflow`", content)
        self.assertIn("`$pennix-trellis-asset-check` 只做只读诊断", content)

    def test_owner_and_execution_carrier_are_separate(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("先判断请求和交付范围，再选择工具", content)
        self.assertIn("普通本地文件、非交互命令", content)
        self.assertIn("执行载体不改变负责组件", content)
        self.assertIn("若基础工具按正确原生调用仍不可用，保留原错误并停止", content)
        self.assertIn("本次所需身份、参数、退出码与回执均可保留", content)

    def test_output_quality_route_preserves_language_and_lifecycle_boundaries(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "`$pennix-agent-output-quality`",
            "复杂交付或批准前方案展示",
            "中文技术内容再组合 `$pennix-chinese-tech-writing`",
            "简单事实走短路径",
            "不改变任务状态、批准或安装 owner",
        ):
            self.assertIn(marker, content)

    def test_execution_details_delegate_to_the_resolvable_integration_contract(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", content)
        specialist = SKILL.parents[1] / "pennix-context-mode-integration" / "SKILL.md"
        self.assertTrue(specialist.is_file())
        self.assertIn(specialist.resolve(), [(SKILL.parent / link).resolve() for link in links])

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
            "宿主 continuation 保留原生入口",
        ):
            self.assertIn(invariant, route)


if __name__ == "__main__":
    unittest.main()
