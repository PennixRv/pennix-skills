#!/usr/bin/env python3
"""Validate a candidate worker report and print a bounded summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import ContractError, report_summary, validate_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--batch")
    parser.add_argument("--instance")
    parser.add_argument("--scope", action="append")
    parser.add_argument("--role")
    parser.add_argument("--lens")
    parser.add_argument("--evidence-method")
    args = parser.parse_args()
    try:
        payload = validate_report(
            args.report,
            expected_task=args.task,
            expected_batch=args.batch,
            expected_instance=args.instance,
            expected_scope=args.scope,
            expected_role=args.role,
            expected_lens=args.lens,
            expected_evidence_method=args.evidence_method,
        )
    except ContractError as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": "valid", **report_summary(payload)}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
