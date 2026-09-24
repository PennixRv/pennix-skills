from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class FastCtxRoutingContractTest(unittest.TestCase):
    def test_native_workflow_protocols_are_excluded_before_fastctx(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "Trellis task",
            "正式 handoff",
            "`request_user_input`",
            "Hook",
            "owner\ncontrolled TUI",
            "必须直接调用其原生接口",
            "绝不以 `run`",
        ):
            self.assertIn(marker, content)

    def test_external_retrieval_owners_are_not_fastctx_adapters(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("`grok-search`", content)
        self.assertIn("不调用、代替或吸收其检索协议", content)

    def test_owner_executable_transport_is_forbidden_but_posthoc_read_is_allowed(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "semantic owner preflight",
            "专用 owner 的 executable 或 CLI 禁止通过 FastCtx `run`",
            "`run_background`",
            "`replace`",
            "保留 blocked/capability-gap 结果",
            "owner 已完成后读取已批准的普通结果",
        ):
            self.assertIn(marker, content)

        grok = (SKILL.parents[1] / "grok-search" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("must be launched through the host's native", grok)
        self.assertIn("Do not start it with `mcp__fastctx.run`", grok)
        self.assertIn("FastCtx may read an approved ordinary result file", grok)


if __name__ == "__main__":
    unittest.main()
