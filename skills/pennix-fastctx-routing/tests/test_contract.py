from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class FastCtxRoutingContractTest(unittest.TestCase):
    def test_native_tool_availability_is_not_inferred_from_exec_nested_tools(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`functions.exec` 中的嵌套编排器", content)
        self.assertIn("不是宿主原生 MCP 清单", content)
        self.assertIn("调用已暴露工具遇到 schema、权限、传输或", content)

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
        self.assertIn("`grok-search`", content)
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

        grok = (SKILL.parents[1] / "grok-search" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("必须通过宿主原生直接命令路径启动", grok)
        self.assertIn("不要用 `mcp__fastctx.run`", grok)
        self.assertIn("FastCtx 可以读取已批准的普通结果文件", grok)


if __name__ == "__main__":
    unittest.main()
