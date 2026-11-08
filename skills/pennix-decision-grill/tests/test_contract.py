"""Prompt contract checks; these do not evaluate actual model behavior."""
from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class DecisionGrillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = SKILL.read_text(encoding="utf-8")

    def test_single_consequential_choice_qualifies_but_facts_do_not(self) -> None:
        for marker in ("一个重要选择就足够", "代理核验可查事实", "不重复问已定事项", "边界清楚的只读研究直接完成证据"):
            self.assertIn(marker, self.content)

    def test_dependencies_precede_priority_and_questions_can_emerge_later(self) -> None:
        for marker in ("依赖和所需证据已满足", "再按影响与阻断优先级排序", "后序留到之后的轮次", "后序问题可能因回答新出现", "不以凑批次"):
            self.assertIn(marker, self.content)

    def test_decision_space_and_solution_design_prior_art_review_are_conditional(self) -> None:
        for marker in (
            "决策空间构造与归并按问题复杂度选择清单、表格或决策树",
            "只有选项之间存在会改变后续分支的依赖或条件时，才需要决策树",
            "该阶段可触发 prior-art review",
            "解决方案设计与收敛在接受正式方案前核验相关流行开源实现或公开提案",
            "新项目和长期维护项目的大型重构尤其应检查这类参考",
            "不自动变成硬性约束",
        ):
            self.assertIn(marker, self.content)

    def test_custom_partial_and_changed_answers_preserve_actual_decisions(self) -> None:
        for marker in ("按实际意图记录", "部分回答只关闭已答节点", "只重开受影响的决定", "保留旧结论与原因", "回答到来后继续规划"):
            self.assertIn(marker, self.content)

    def test_evidence_does_not_erase_the_decision_checkpoint_or_choose_for_user(self) -> None:
        for marker in ("先在当前任务保存", "返回动作", "teammate 只交报告", "不加轮询或另一套调度器", "证据与依赖尚未完成", "空列表不等于整体方案获接受"):
            self.assertIn(marker, self.content)

    def test_required_unanswered_question_never_becomes_a_timed_default(self) -> None:
        for marker in ("原生阻塞式 `request_user_input`", "不因时间默认采用推荐", "保留必要未决项并停止其依赖动作", "可选问题空回执服从更高优先级宿主合同"):
            self.assertIn(marker, self.content)

    def test_native_interaction_is_not_discovered_through_nested_mcp_tools(self) -> None:
        for marker in (
            "属于宿主原生交互",
            "不要求出现在 MCP 或嵌套工具清单中",
            "不能证明宿主直接工具不存在",
            "不要用嵌套清单探测或判断交互工具可用性",
            "不改报为工具缺失",
        ):
            self.assertIn(marker, self.content)

    def test_material_execution_choice_uses_native_phase_while_small_addition_can_continue(self) -> None:
        for marker in ("说明问题、影响和推荐", "已授权的局部工程选择", "execution 自然落点后继续", "回最早受影响阶段", "不手改 `task.json`", "重新核验受影响接受及授权", "不创建第二状态机"):
            self.assertIn(marker, self.content)
        self.assertNotIn("仅允许 `in_progress` 的 `replan`", self.content)

    def test_final_review_preserves_separate_acceptance_and_authorization(self) -> None:
        review = self.content.split("## 最终方案复核", 1)[1].split("## 执行中的新选择", 1)[0]
        self.assertLess(review.index("先展示完整方案"), review.index("按宿主交互合同询问"))
        self.assertIn("trellis-solution-design-and-convergence", review)
        self.assertNotIn("原生 `plan seal`", review)
        for marker in ("只接受方案时不推定实施授权", "分别交原生接口记录", "不要求口令", "空回执、取消", "已有充分整体授权不重复询问", "实质变化回最早受影响阶段", "不盲目重做已成功的动作"):
            self.assertIn(marker, review)

    def test_plan_review_gate_precedes_final_plan_display(self) -> None:
        gate = self.content.split("## 方案审查闸门", 1)[1].split("## 最终方案复核", 1)[0]
        for marker in (
            "方案和任务材料形成后",
            "实际修改目标与 owner",
            "证据或合同问题",
            "用户取舍问题",
            "已知限制",
            "复核受影响材料",
            "实质矛盾未解决时不请求整体批准",
            "不新增 Trellis 或 Teamwork 状态",
        ):
            self.assertIn(marker, gate)
        self.assertIn("独立复核不强制另派代理", gate)

    def test_approval_research_and_continue_keep_their_distinct_boundaries(self) -> None:
        for marker in ("逐项设计问答不等于用户认可整体方案", "纯分析完成证据不要求实施批准", "纳入规划不等于实施批准", "普通继续或充分压缩断点复用已知决定", "模型行为的确定性保证"):
            self.assertIn(marker, self.content)

    def test_extra_findings_return_to_the_mainline_and_keep_approval_distinct(self) -> None:
        for marker in (
            "先核验其是否真实",
            "纳入当前任务",
            "记录后另建任务",
            "当前范围已有覆盖",
            "明确排除",
            "不能静默丢弃",
            "纳入规划不等于实施批准",
            "回读原始请求、主线决策和未决项",
            "不能让额外发现取代主线",
        ):
            self.assertIn(marker, self.content)


if __name__ == "__main__":
    unittest.main()
