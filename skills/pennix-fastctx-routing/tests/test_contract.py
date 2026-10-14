from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class FastCtxRoutingContractTest(unittest.TestCase):
    def test_native_tool_availability_is_not_inferred_from_exec_nested_tools(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`functions.exec` 中的嵌套编排器", content)
        self.assertIn("不是宿主原生 MCP 清单", content)
        self.assertIn("调用已暴露工具遇到 schema、权限、传输或", content)
        self.assertIn("不能从该嵌套调用面调用", content)
        self.assertIn("不能只查 `ALL_TOOLS` 得出缺失结论", content)

    def test_capacity_and_partial_results_do_not_trigger_fallback(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "单次输出预算耗尽、可恢复的分页限制",
            "也不结束当前工作",
            "Partial 只按结果给出的精确 offset/files/after_seq 续读",
            "不等待新的用户轮次",
            "容量提示不触发 shell fallback",
            "不关闭 provider 保护",
            "不自动降级",
        ):
            self.assertIn(marker, content)

    def test_fastctx_parameter_names_are_canonical_and_errors_are_routed_to_the_owner(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "只使用 FastCtx `tools/list` 发布的规范字段",
            "单文件顶层使用 `file_path`",
            "批量条目使用 `path`",
            "`grep` 使用必填 `pattern`",
            "`run` 使用 `command`、`cwd`、`timeout_ms`、`login_shell` 和 `encoding`",
            "不增加或猜测别名",
            "failed to deserialize parameters",
        ):
            self.assertIn(marker, content)

    def test_native_workflow_protocols_are_excluded_before_fastctx(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "Trellis 任务状态",
            "正式交接",
            "`request_user_input`",
            "Hook",
            "原生 Plugin/MCP/TUI",
            "对应组件或宿主规定的接口",
            "不转交 FastCtx",
        ):
            self.assertIn(marker, content)

    def test_external_retrieval_owners_are_not_fastctx_adapters(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`$pennix-grok-search`", content)
        self.assertIn("不得调用、代替或推进检索协议", content)

    def test_owner_executable_transport_is_forbidden_but_posthoc_read_is_allowed(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "先按操作语义区分",
            "命令禁止通过 FastCtx `run`",
            "`run_background`",
            "`replace`",
            "保留 `blocked`/`capability-gap` 结果",
            "完成调用并产生已批准的普通本地结果文件后",
        ):
            self.assertIn(marker, content)

        grok = (SKILL.parents[1] / "pennix-grok-search" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("必须通过宿主原生直接命令路径启动", grok)
        self.assertIn("不要用 `mcp__fastctx.run`", grok)
        self.assertIn("FastCtx 可以读取已批准的普通结果文件", grok)


if __name__ == "__main__":
    unittest.main()
