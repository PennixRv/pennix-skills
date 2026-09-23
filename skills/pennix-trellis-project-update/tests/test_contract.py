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
            "`.trellis/.template-hashes.json`",
        ):
            self.assertIn(marker, content)

    def test_ownership_and_latest_workflow_boundaries_are_explicit(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        for marker in (
            "$pennix-workflow-lifecycle",
            "workflow-doctor",
            "$pennix-decision-gates",
            "inline main-session delivery",
            "explicitly requested independent evidence",
            "immutable ref",
            "Do not copy files from a Trellis checkout",
        ):
            self.assertIn(marker, content)

    def test_destructive_paths_are_not_default(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("Do not use `--force` as the default", content)
        self.assertIn("Never hand-edit", content)
        self.assertIn("Do not guess, force, or report completion", content)


if __name__ == "__main__":
    unittest.main()
