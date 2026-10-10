from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class TrellisProjectUpdateContractTest(unittest.TestCase):
    def test_frontmatter_and_native_update_contract(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "name: pennix-trellis-project-update",
            "trellis update --dry-run",
            "trellis update --create-new",
            "trellis update --skip-all",
            "--migrate",
            "trellis workflow --list",
            "trellis workflow --verify",
            "`.trellis/workflow-provenance.json`",
            "逐字相同的 sidecar",
            "宽泛的 `find ... -delete`",
            "`.trellis/.template-hashes.json`",
        ):
            self.assertIn(marker, content)

    def test_ownership_and_latest_workflow_boundaries_are_explicit(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "$pennix-workflow-lifecycle",
            "workflow-doctor",
            "$pennix-decision-grill",
            "主会话内联交付",
            "明确要求的独立证据",
            "不可变引用",
            "`.trellis/workflow.md.new`",
            "不要从 Trellis 检出目录复制文件",
        ):
            self.assertIn(marker, content)

    def test_destructive_paths_are_not_default(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("不要默认使用 `--force`", content)
        self.assertIn("不得手改", content)
        self.assertIn("不要猜测、强制操作或声称完成", content)


if __name__ == "__main__":
    unittest.main()
