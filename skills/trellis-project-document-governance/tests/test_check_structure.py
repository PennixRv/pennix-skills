from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_structure.py"
SPEC = importlib.util.spec_from_file_location("check_structure", SCRIPT)
assert SPEC and SPEC.loader
CHECK_STRUCTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_STRUCTURE)


class MarkdownLinkExtractionTests(unittest.TestCase):
    def check_markdown(self, content: str, files: dict[str, str] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative_path, value in (files or {}).items():
                target = root / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(value, encoding="utf-8")
            document = root / "document.md"
            document.write_text(content, encoding="utf-8")
            return CHECK_STRUCTURE.check_text(root, document)

    def test_inline_code_link_example_is_ignored(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\nExample: `[sample](missing-inline.md)`.\n"
        )

        self.assertEqual(errors, [])

    def test_matching_multibacktick_code_span_is_ignored(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\nExample: ``[sample](missing-multi.md)``.\n"
        )

        self.assertEqual(errors, [])

    def test_unclosed_code_span_is_ignored_to_end_of_document(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\nExample: `[sample](missing-unclosed.md)\n"
        )

        self.assertEqual(errors, [])

    def test_fenced_code_link_examples_are_ignored(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\n```markdown\n[sample](missing-fence.md)\n```\n\n"
            "~~~~\n[sample](missing-tilde.md)\n~~~~\n"
        )

        self.assertEqual(errors, [])

    def test_fenced_code_heading_is_ignored(self) -> None:
        errors = self.check_markdown("# Heading\n\n```text\n#not-a-heading\n```\n")

        self.assertEqual(errors, [])

    def test_body_pseudo_heading_still_fails(self) -> None:
        errors = self.check_markdown("#not-a-heading\n")

        self.assertEqual(errors, ["document.md:1: heading needs a space"])

    def test_real_link_after_code_example_is_checked(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\n`[sample](missing-code.md)`\n\n[real](missing-real.md)\n"
        )

        self.assertEqual(errors, ["document.md: missing link target: missing-real.md"])

    def test_long_fence_does_not_close_on_shorter_run(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\n````markdown\n[sample](missing-code.md)\n```\n"
            "still code\n````\n\n[real](missing-real.md)\n"
        )

        self.assertEqual(errors, ["document.md: missing link target: missing-real.md"])

    def test_real_existing_link_still_passes(self) -> None:
        errors = self.check_markdown(
            "# Heading\n\n[real](existing.md)\n",
            {"existing.md": "# Existing\n"},
        )

        self.assertEqual(errors, [])

    def test_real_outside_link_still_fails(self) -> None:
        errors = self.check_markdown("# Heading\n\n[real](../outside.md)\n")

        self.assertEqual(errors, ["document.md: link outside root: ../outside.md"])

    def test_links_only_ignores_non_link_structure_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "document.md"
            document.write_text(
                "# Heading  \n\n```text\n#not-a-heading\n```\n\n[real](missing.md)\n",
                encoding="utf-8",
            )

            errors = CHECK_STRUCTURE.check_text(root, document, links_only=True)

        self.assertEqual(errors, ["document.md: missing link target: missing.md"])

    @patch.object(CHECK_STRUCTURE.subprocess, "run")
    def test_tracked_markdown_discards_disappeared_index_paths(self, run: unittest.mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            current = root / "archive" / "document.md"
            current.parent.mkdir()
            current.write_text("# Heading\n", encoding="utf-8")
            run.return_value = SimpleNamespace(
                returncode=0,
                stdout=b"active/document.md\0archive/document.md\0",
                stderr=b"",
            )

            paths, errors = CHECK_STRUCTURE.collect_tracked_markdown_files(root, max_files=10)

        self.assertEqual(errors, [])
        self.assertEqual(paths, [current.resolve()])


if __name__ == "__main__":
    unittest.main()
