#!/usr/bin/env python3
"""Regression coverage for same-revision independent-review validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/check_gate.py"


def report(*, result_id: str, instance: str, lens: str, evidence_id: str) -> dict[str, object]:
    return {
        "schema_version": 3,
        "result_id": result_id,
        "task_id": "task-a",
        "batch_id": "batch-a",
        "role_id": "auditor",
        "instance_id": instance,
        "status": "complete",
        "scope": ["skills/review-gate"],
        "lens": lens,
        "evidence_method": "read source",
        "evidence": [
            {
                "id": evidence_id,
                "kind": "file",
                "locator": "skills/review-gate/SKILL.md",
                "claim": "The review gate is documented.",
                "verified": True,
            }
        ],
        "findings": [],
    }


class CheckGateTests(unittest.TestCase):
    def run_gate(self, primary: Path, counter: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--primary", str(primary), "--counter", str(counter), "--risk", "major"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_gate_passes_for_different_assigned_lenses(self) -> None:
        with tempfile.TemporaryDirectory(prefix="review-gate-") as directory:
            root = Path(directory)
            primary = report(result_id="result-a", instance="worker-a", lens="primary-lens", evidence_id="e1")
            counter = report(result_id="result-b", instance="worker-b", lens="counter-lens", evidence_id="e2")
            counter.update(
                {
                    "review_round": 1,
                    "review_of": ["result-a"],
                    "review_relation": "independent",
                    "review_verdict": "supports",
                    "evidence_refs": ["e2"],
                    "coverage": "complete",
                }
            )
            primary_path = root / "primary.json"
            counter_path = root / "counter.json"
            primary_path.write_text(json.dumps(primary), encoding="utf-8")
            counter_path.write_text(json.dumps(counter), encoding="utf-8")
            completed = self.run_gate(primary_path, counter_path)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "passed")

    def test_gate_rejects_equal_assigned_lenses(self) -> None:
        with tempfile.TemporaryDirectory(prefix="review-gate-") as directory:
            root = Path(directory)
            primary = report(result_id="result-a", instance="worker-a", lens="shared-lens", evidence_id="e1")
            counter = report(result_id="result-b", instance="worker-b", lens="shared-lens", evidence_id="e2")
            counter.update(
                {
                    "review_round": 1,
                    "review_of": ["result-a"],
                    "review_relation": "independent",
                    "review_verdict": "supports",
                    "evidence_refs": ["e2"],
                    "coverage": "complete",
                }
            )
            primary_path = root / "primary.json"
            counter_path = root / "counter.json"
            primary_path.write_text(json.dumps(primary), encoding="utf-8")
            counter_path.write_text(json.dumps(counter), encoding="utf-8")
            completed = self.run_gate(primary_path, counter_path)
            self.assertEqual(completed.returncode, 2)
            self.assertIn("distinct assigned lens", completed.stdout)


if __name__ == "__main__":
    unittest.main()
