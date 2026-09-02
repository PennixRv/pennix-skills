#!/usr/bin/env python3
"""Check the minimum independent-review relationship between two reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from workflow_contracts import ContractError, validate_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", required=True, type=Path)
    parser.add_argument("--counter", required=True, type=Path)
    parser.add_argument("--risk", choices=("major", "critical"), required=True)
    args = parser.parse_args()
    try:
        primary = validate_report(args.primary)
        counter = validate_report(args.counter, primary["task_id"], primary["batch_id"])
        if primary["status"] != "complete" or counter["status"] != "complete":
            raise ContractError("both reports must be complete before the gate can pass")
        if primary["instance_id"] == counter["instance_id"]:
            raise ContractError("primary and counter reports must come from different instances")
        if primary["scope"] != counter["scope"]:
            raise ContractError("primary and counter scopes must match exactly")
        if "review_of" not in counter or primary["result_id"] not in counter["review_of"]:
            raise ContractError("counter report must identify the primary result in review_of")
        if counter.get("review_relation") != "independent":
            raise ContractError("counter report must declare an independent review relation")
        if counter.get("review_lens") in {None, primary.get("review_lens")}:
            raise ContractError("counter report must use a distinct review_lens")
        primary_evidence_ids = {item["id"] for item in primary["evidence"]}
        counter_evidence_ids = {item["id"] for item in counter["evidence"]}
        if primary_evidence_ids & counter_evidence_ids:
            raise ContractError("primary and counter reports must not reuse evidence ids")
        if counter.get("coverage") != "complete":
            raise ContractError("counter report coverage is not complete")
        print(json.dumps({
            "status": "passed",
            "risk": args.risk,
            "primary": primary["result_id"],
            "counter": counter["result_id"],
            "verdict": counter["review_verdict"],
        }, ensure_ascii=True, sort_keys=True))
        return 0
    except ContractError as exc:
        print(json.dumps({"status": "insufficient_independent_review", "reason": str(exc)}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
