#!/usr/bin/env python3
"""Regression coverage for extracted candidate reports and the report contract."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
CONTRACTS = SKILL / "scripts/workflow_contracts.py"
EXTRACTOR = SKILL / "scripts/extract_channel_report.py"

CONTRACT_SPEC = importlib.util.spec_from_file_location("evidence_contracts", CONTRACTS)
assert CONTRACT_SPEC is not None and CONTRACT_SPEC.loader is not None
contracts = importlib.util.module_from_spec(CONTRACT_SPEC)
CONTRACT_SPEC.loader.exec_module(contracts)

EXTRACT_SPEC = importlib.util.spec_from_file_location("extract_channel_report", EXTRACTOR)
assert EXTRACT_SPEC is not None and EXTRACT_SPEC.loader is not None
extractor = importlib.util.module_from_spec(EXTRACT_SPEC)
EXTRACT_SPEC.loader.exec_module(extractor)


def report(*, lens: str = "primary-lens", evidence_method: str = "read source") -> dict[str, object]:
    return {
        "schema_version": 3,
        "result_id": "result-a",
        "task_id": "task-a",
        "batch_id": "batch-a",
        "role_id": "auditor",
        "instance_id": "worker-a",
        "status": "complete",
        "scope": ["skills/evidence-report"],
        "lens": lens,
        "evidence_method": evidence_method,
        "evidence": [
            {
                "id": "e1",
                "kind": "file",
                "locator": "skills/evidence-report/SKILL.md",
                "claim": "The candidate contract is documented.",
                "verified": True,
            }
        ],
        "findings": [],
    }


class CandidateReportTests(unittest.TestCase):
    def test_validator_binds_role_lens_and_evidence_method(self) -> None:
        with tempfile.TemporaryDirectory(prefix="candidate-report-") as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report()), encoding="utf-8")
            payload = contracts.validate_report(
                path,
                expected_task="task-a",
                expected_batch="batch-a",
                expected_instance="worker-a",
                expected_scope=["skills/evidence-report"],
                expected_role="auditor",
                expected_lens="primary-lens",
                expected_evidence_method="read source",
            )
            self.assertEqual(payload["schema_version"], 3)
            with self.assertRaisesRegex(contracts.ContractError, "expected lens"):
                contracts.validate_report(path, expected_lens="counter-lens")

    def test_extractor_requires_one_wrapped_report_after_send_sequence(self) -> None:
        payload = report()
        events = [
            {"seq": 7, "kind": "message", "by": "main", "text": "assignment"},
            {"seq": 8, "kind": "say", "by": "worker-a", "text": "ordinary progress"},
            {
                "seq": 9,
                "kind": "say",
                "by": "worker-a",
                "text": "<CANDIDATE_REPORT>\n%s\n</CANDIDATE_REPORT>" % json.dumps(payload),
            },
        ]
        self.assertEqual(extractor.extract(events, "worker-a", 7), payload)
        with self.assertRaisesRegex(extractor.ContractError, "exactly one"):
            extractor.extract(events, "worker-a", 9)

    def test_legacy_duplicate_review_lens_is_rejected(self) -> None:
        payload = report()
        payload["review_lens"] = "legacy-lens"
        with tempfile.TemporaryDirectory(prefix="candidate-report-") as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(contracts.ContractError, "unknown"):
                contracts.validate_report(path)


if __name__ == "__main__":
    unittest.main()
