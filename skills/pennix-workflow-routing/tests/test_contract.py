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
        self.assertIn((SKILL.parents[1] / "pennix-context-mode-integration/SKILL.md").resolve(), targets)
        self.assertIn((SKILL.parent / "references/knowledge-promotion.md").resolve(), targets)

    def test_phase_routing_keeps_stage_skills_distinct_and_optional_components_conditional(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "| 目标探索与需求核对 |",
            "| 决策空间构造与归并 |",
            "| 解决方案设计与收敛 |",
            "| 任务实施 |",
            "| 交付审查与收尾 |",
            "只有选项依赖、条件分支会改变后续决策时才展开决策树",
            "触发 prior-art review 时",
            "Trellis CLI 接受阶段结果",
            "当前宿主声明的 `prototype`",
            "当前宿主声明的 `codebase-design`",
            "当前宿主声明的 `diagnosing-bugs`",
            "codebase-design` 仅在实施中确有模块接口或边界设计问题时提供方法",
            "`trellis-break-loop` 按需处理",
            "不是目标 Trellis fork 的 bundled 依赖",
            "未选能力不列为该路线前置条件",
            "不是阶段转换、实施或任务完成的前置条件",
        ):
            self.assertIn(marker, content)
        self.assertIn("组件按当前需要参与，不是每个阶段的必备清单", content)

    def test_external_search_prefers_tavily_and_routes_grok_conditionally(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("优先 `$pennix-tavily-search`", content)
        self.assertIn("当前操作适合 Grok 或用户/路线明确选择 Grok", content)
        self.assertIn("Tavily 操作失败时遵循其 Skill 的失败合同", content)
        self.assertIn("不自动重试或改用其他服务商", content)
        self.assertIn("才可将同一个有界请求交给自托管 `$pennix-tavily-search` 一次", content)


if __name__ == "__main__":
    unittest.main()
