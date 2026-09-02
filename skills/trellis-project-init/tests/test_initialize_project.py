#!/usr/bin/env python3
"""Contract tests for the deterministic Trellis project initializer."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SKILL = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(SKILL / "scripts"))

import initialize_project  # noqa: E402


class InitializeProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="trellis-project-init-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def runner(calls: list[list[str]]):
        def run(command: list[str], **_: object) -> SimpleNamespace:
            calls.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        return run

    def test_rejects_relative_and_broad_roots(self) -> None:
        with self.assertRaisesRegex(initialize_project.InitializationError, "absolute"):
            initialize_project.resolve_project_root(".")
        with self.assertRaisesRegex(initialize_project.InitializationError, "global_or_broad"):
            initialize_project.resolve_project_root(str(Path.home()))

    def test_trellis_only_uses_noninteractive_exact_command(self) -> None:
        calls: list[list[str]] = []
        result = initialize_project.run_initialization(
            root=self.root,
            mode="trellis-only",
            developer="penn",
            dry_run=False,
            runner=self.runner(calls),
        )
        self.assertEqual(result["status"], "initialized")
        self.assertEqual(calls, [[
            "trellis", "init", "--yes", "--codex", "--workflow",
            "channel-driven-subagent-dispatch", "--skip-existing", "-u", "penn",
        ]])
        self.assertNotIn("--force", calls[0])

    def test_dry_run_does_not_call_trellis(self) -> None:
        calls: list[list[str]] = []
        result = initialize_project.run_initialization(
            root=self.root,
            mode="trellis-only",
            developer="penn",
            dry_run=True,
            runner=self.runner(calls),
        )
        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["trellis"], "would_run")
        self.assertEqual(calls, [])

    def test_removed_mode_is_not_supported(self) -> None:
        with self.assertRaisesRegex(initialize_project.InitializationError, "unsupported_initialization_mode"):
            initialize_project.run_initialization(
                root=self.root,
                mode="deprecated-mode",
                developer="penn",
                dry_run=True,
                runner=self.runner([]),
            )


if __name__ == "__main__":
    unittest.main()
