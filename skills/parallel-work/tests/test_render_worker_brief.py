#!/usr/bin/env python3
"""Regression coverage for the bounded candidate-worker brief renderer."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/render_worker_brief.py"
SPEC = importlib.util.spec_from_file_location("render_worker_brief", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def request() -> dict[str, object]:
    return {
        "question": "Does the candidate contract preserve the assigned evidence method?",
        "scope": ["skills/evidence-report", "skills/review-gate"],
        "lens": "contract-integrity",
        "role_id": "contract-auditor",
        "evidence_method": "read source and run the targeted tests",
    }


class RenderWorkerBriefTests(unittest.TestCase):
    def test_primary_brief_preserves_all_assignment_fields(self) -> None:
        rendered = renderer.render(
            request(), task="audit-1", batch="batch-1", instance="worker-a", counter_of=None, review_round=1
        )
        self.assertIn("<CANDIDATE_REPORT>", rendered)
        self.assertIn('"role_id": "contract-auditor"', rendered)
        self.assertIn('"lens": "contract-integrity"', rendered)
        self.assertIn('"evidence_method": "read source and run the targeted tests"', rendered)
        self.assertIn('"schema_version": 3', rendered)
        self.assertNotIn("review_of", rendered)

    def test_counter_brief_requires_a_primary_identity(self) -> None:
        rendered = renderer.render(
            request(), task="audit-1", batch="batch-1", instance="worker-b", counter_of="result-a", review_round=2
        )
        self.assertIn('"review_of": ["result-a"]', rendered)
        self.assertIn('"review_relation": "independent"', rendered)

    def test_output_rejects_an_unsafe_identifier(self) -> None:
        with self.assertRaisesRegex(renderer.ContractError, "task is invalid"):
            renderer.render(
                request(), task="audit\n1", batch="batch-1", instance="worker-a", counter_of=None, review_round=1
            )

    def test_cli_writes_the_same_rendered_text(self) -> None:
        with tempfile.TemporaryDirectory(prefix="worker-brief-") as directory:
            root = Path(directory)
            request_path = root / "request.json"
            output = root / "brief.md"
            request_path.write_text(json.dumps(request()), encoding="utf-8")
            original = sys.argv
            try:
                sys.argv = [
                    str(SCRIPT), "--request", str(request_path), "--task", "audit-1", "--batch", "batch-1",
                    "--instance", "worker-a", "--output", str(output),
                ]
                self.assertEqual(renderer.main(), 0)
            finally:
                sys.argv = original
            self.assertIn("Trellis Candidate Work", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
