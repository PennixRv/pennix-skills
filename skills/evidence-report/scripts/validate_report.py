#!/usr/bin/env python3
"""Validate a candidate worker report and print a bounded summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from workflow_contracts import ContractError, report_summary, validate_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--batch")
    parser.add_argument("--instance")
    parser.add_argument("--scope", action="append")
    args = parser.parse_args()
    try:
        payload = validate_report(args.report, args.task, args.batch, args.instance, args.scope)
    except ContractError as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": "valid", **report_summary(payload)}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
