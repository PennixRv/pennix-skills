#!/usr/bin/env python3
"""Regression tests for candidate request output safety."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/build_request.py"
SPEC = importlib.util.spec_from_file_location("build_request", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class BuildRequestTests(unittest.TestCase):
    def test_output_symlink_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="build-request-") as directory:
            root = Path(directory)
            target = root / "target.json"
            output = root / "normalized.json"
            target.write_text("keep\n", encoding="utf-8")
            output.symlink_to(target)
            with self.assertRaisesRegex(builder.ContractError, "regular file"):
                builder.write_output(output, "replace\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")

    def test_symlink_parent_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="build-request-") as directory:
            root = Path(directory)
            target = root / "target"
            target.mkdir()
            parent = root / "nested"
            parent.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(builder.ContractError, "symbolic path"):
                builder.write_output(parent / "normalized.json", "replace\n")

    def test_output_is_replaced_atomically(self) -> None:
        with tempfile.TemporaryDirectory(prefix="build-request-") as directory:
            output = Path(directory) / "nested" / "normalized.json"
            builder.write_output(output, "{\"ok\": true}\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "{\"ok\": true}\n")
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
