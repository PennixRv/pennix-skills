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

    def test_custom_partial_and_changed_answers_preserve_actual_decisions(self) -> None:
        for marker in ("按实际意图记录", "部分回答只关闭已答节点", "只重开受影响的决定", "保留旧结论与原因", "回答到来后继续规划"):
            self.assertIn(marker, self.content)

    def test_evidence_does_not_erase_the_decision_checkpoint_or_choose_for_user(self) -> None:
        for marker in ("先在当前task保存", "返回动作", "子节点核验事实，不选择用户取舍", "不加轮询或另一个调度器", "证据/依赖尚未完成", "不得依据空列表直接封口"):
            self.assertIn(marker, self.content)

    def test_required_unanswered_question_never_becomes_a_timed_default(self) -> None:
        for marker in ("原生阻塞request_user_input", "不因时间默认采用推荐", "保留必要未决项并停止其依赖动作", "可选问题空回执服从更高优先级宿主合同"):
            self.assertIn(marker, self.content)

    def test_material_execution_choice_uses_native_phase_while_small_addition_can_continue(self) -> None:
        for marker in ("立即说明问题、影响与推荐", "先原生task.py replan回planning", "任务已在planning时更新并重新seal", "不手改task.json", "该请求只授权精确增量", "不创建第二状态机"):
            self.assertIn(marker, self.content)

    def test_approval_research_and_continue_keep_their_distinct_boundaries(self) -> None:
        for marker in ("设计回答不授予实施权", "analysis_only完成证据不要求实施seal/批准", "专门批准", "普通继续或充分压缩断点复用已知决定", "模型行为的确定性保证"):
            self.assertIn(marker, self.content)


if __name__ == "__main__":
    unittest.main()
