from pathlib import Path
import re
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class WorkflowRoutingContractTest(unittest.TestCase):
    # Static integrity only; routing behavior requires actual tool-call evidence.
    def test_routing_parameter_identifiers_remain_available(self) -> None:
        identifiers = set(re.findall(r"`([a-z_]+)`", SKILL.read_text(encoding="utf-8")))
        self.assertFalse({
            "work_domain", "delivery_mode", "execution_class", "decision_frontier",
            "approval_mode", "owner", "allowed_transport", "state_writer",
            "exit_conditions", "replan_trigger",
        } - identifiers)

    def test_named_collection_skills_exist(self) -> None:
        names = set(re.findall(r"\$(pennix-[a-z0-9-]+)", SKILL.read_text(encoding="utf-8")))
        self.assertTrue(names)
        for name in names:
            with self.subTest(skill=name):
                self.assertTrue((SKILL.parents[1] / name / "SKILL.md").is_file())

    def test_relative_links_resolve_from_the_loaded_skill_directory(self) -> None:
        links = re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", SKILL.read_text(encoding="utf-8"))
        targets = []
        for link in links:
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link):
                continue
            with self.subTest(link=link):
                target = (SKILL.parent / link).resolve()
                self.assertTrue(target.is_file())
                targets.append(target)
        self.assertNotIn("pennix-context-mode-integration", SKILL.read_text(encoding="utf-8"))
        self.assertIn((SKILL.parent / "references/knowledge-promotion.md").resolve(), targets)

    def test_phase_routing_keeps_stage_skills_distinct_and_optional_components_conditional(self) -> None:
        content = (SKILL.parent / "references/phase-routing.md").read_text(encoding="utf-8")
        for marker in (
            "| 目标探索与需求核对阶段 |",
            "| 决策空间构造与归并阶段 |",
            "| 解决方案设计与收敛阶段 |",
            "| 任务实施与测试验证阶段 |",
            "| 交付审查与现场收尾阶段 |",
            "只有选项依赖或条件分支会改变后续决策时才展开决策树",
            "触发 prior-art review 时",
            "Trellis CLI 接受阶段结果",
            "当前宿主声明的 `codebase-design`",
            "`diagnosing-bugs` 仅在难定位缺陷或性能回退需要系统诊断时参与",
            "`trellis-break-loop` 按需处理",
            "不是目标 Trellis fork 的 bundled 依赖",
            "未选能力不列为该路线前置条件",
            "不是阶段转换、实施或任务完成的前置条件",
        ):
            self.assertIn(marker, content)
        self.assertIn("组件按当前需要参与，不是每个阶段的必备清单", content)
        phase_section = content
        phase_rows = [
            line for line in phase_section.splitlines()
            if line.startswith((
                "| 目标探索与需求核对阶段 |",
                "| 决策空间构造与归并阶段 |",
                "| 解决方案设计与收敛阶段 |",
                "| 任务实施与测试验证阶段 |",
                "| 交付审查与现场收尾阶段 |",
            ))
        ]
        self.assertTrue(phase_rows)
        self.assertTrue(all("trellis-idea-to-closed-plan" not in line for line in phase_rows))
        phase_skill_slugs = (
            "trellis-goal-exploration-and-requirements",
            "trellis-decision-space-construction-and-merging",
            "trellis-solution-design-and-convergence",
            "trellis-task-implementation",
            "trellis-delivery-review-and-closeout",
        )
        for row, slug in zip(phase_rows, phase_skill_slugs):
            with self.subTest(phase_skill=slug):
                self.assertIn(f"`{slug}`", row)
        delivery_row = next(line for line in phase_rows if line.startswith("| 交付审查与现场收尾阶段 |"))
        self.assertIn("只有存在必要用户决定或合同要求用户接受时", delivery_row)
        self.assertIn("`pennix-decision-grill`", delivery_row)

    def test_external_search_prefers_tavily_and_routes_grok_conditionally(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("优先 `$pennix-tavily-search`", content)
        self.assertIn("仅在当前操作适合 Grok（例如需要 X 来源）或用户/路线明确选择 Grok", content)
        self.assertIn("Tavily 操作失败时遵循其 Skill 的失败合同", content)
        self.assertIn("不自动重试或改用其他服务商", content)
        self.assertNotIn("普通外部检索必须先走 `$pennix-grok-search`", content)


if __name__ == "__main__":
    unittest.main()
