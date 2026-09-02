#!/usr/bin/env python3
"""Validate and emit a Trellis candidate-work request; never starts a worker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from workflow_contracts import ContractError, _text, _text_list, load_json_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        value = load_json_file(args.input, 64 * 1024)
        allowed = {"question", "scope", "lens", "role_id", "evidence_method", "review_policy"}
        unknown = set(value) - allowed
        if unknown:
            raise ContractError("request has unknown fields: %s" % sorted(unknown))
        result = {
            "schema_version": 1,
            "question": _text(value.get("question"), "question", 8192),
            "scope": _text_list(value.get("scope"), "scope", 64),
            "lens": _text(value.get("lens"), "lens", 256),
            "role_id": _text(value.get("role_id"), "role_id", 128),
            "evidence_method": _text(value.get("evidence_method"), "evidence_method", 2048),
        }
        if not result["scope"]:
            raise ContractError("scope must not be empty")
        policy = value.get("review_policy")
        if policy is not None:
            if not isinstance(policy, dict) or set(policy) != {"mode", "risk", "reason"}:
                raise ContractError("review_policy fields are invalid")
            if policy["mode"] not in {"required", "exempt"} or policy["risk"] not in {"low", "major", "critical"}:
                raise ContractError("review_policy mode or risk is invalid")
            if policy["mode"] == "exempt" and policy["risk"] != "low":
                raise ContractError("only low-risk requests may exempt review")
            result["review_policy"] = {
                "mode": policy["mode"],
                "risk": policy["risk"],
                "reason": _text(policy["reason"], "review_policy.reason", 2048),
            }
        encoded = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
        return 0
    except (ContractError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
