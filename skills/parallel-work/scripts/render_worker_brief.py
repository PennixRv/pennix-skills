#!/usr/bin/env python3
"""Render one bounded Trellis candidate-worker prompt from a validated request."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import (  # noqa: E402
    ContractError,
    _text,
    load_json_file,
    normalize_candidate_request,
    write_output,
)


IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def identifier(value: str, label: str) -> str:
    value = _text(value, label, 128)
    if not IDENTIFIER_RE.fullmatch(value):
        raise ContractError("%s is invalid" % label)
    return value


def render(
    request: dict[str, object],
    *,
    task: str,
    batch: str,
    instance: str,
    counter_of: str | None,
    review_round: int,
) -> str:
    assigned = normalize_candidate_request(request)
    task = identifier(task, "task")
    batch = identifier(batch, "batch")
    instance = identifier(instance, "instance")
    if review_round < 1:
        raise ContractError("review_round must be positive")
    review_block = ""
    if counter_of:
        counter_of = identifier(counter_of, "counter_of")
        review_block = """

Because this is the independent counter view, include these additional fields in the report JSON after completing the work:

```json
{
  "review_round": %d,
  "review_of": ["%s"],
  "review_relation": "independent",
  "review_verdict": "supports | refutes | uncertain",
  "coverage": "complete | partial | blocked"
}
```
""" % (review_round, counter_of)

    assignment = {
        "task_id": task,
        "batch_id": batch,
        "role_id": assigned["role_id"],
        "instance_id": instance,
        "question": assigned["question"],
        "scope": assigned["scope"],
        "lens": assigned["lens"],
        "evidence_method": assigned["evidence_method"],
    }
    report = {
        "schema_version": 3,
        "result_id": "choose-a-stable-result-id",
        "task_id": task,
        "batch_id": batch,
        "role_id": assigned["role_id"],
        "instance_id": instance,
        "status": "complete | incomplete | blocked | error",
        "scope": assigned["scope"],
        "lens": assigned["lens"],
        "evidence_method": assigned["evidence_method"],
        "evidence": [
            {
                "id": "evidence-id",
                "kind": "file | command | url | event",
                "locator": "precise local path, command, URL, or channel event",
                "claim": "what this evidence establishes",
                "verified": True,
            }
        ],
        "findings": [
            {
                "severity": "critical | major | minor | info",
                "claim": "conclusion",
                "impact": "why it matters",
                "reproduce": "how the coordinator can verify it",
                "evidence_ids": ["evidence-id"],
            }
        ],
    }
    return """# Trellis Candidate Work

You are an independent candidate worker. This is a bounded analysis, design critique, audit, review, or verification assignment, not an implementation task.

```json
%s
```

Read any task-relevant project, external, or Internet material needed for this assignment. Do not edit project files, task files, or configuration; do not run Git commands; do not control Trellis lifecycle; and do not dispatch another worker. Your terminal response is captured by Trellis automatically, so do not invoke `trellis channel` yourself.

Return exactly one response, with no prose outside this wrapper:

<CANDIDATE_REPORT>
%s
</CANDIDATE_REPORT>

Replace every illustrative value in the report template with actual evidence. Preserve the assigned `task_id`, `batch_id`, `role_id`, `instance_id`, `scope`, `lens`, and `evidence_method` exactly. A `complete` result needs at least one evidence item. Do not claim acceptance or write project facts; the main session extracts and validates this candidate report before any promotion.%s
""" % (
        json.dumps(assignment, ensure_ascii=False, indent=2),
        json.dumps(report, ensure_ascii=False, indent=2),
        review_block,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--counter-of")
    parser.add_argument("--review-round", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        content = render(
            load_json_file(args.request),
            task=args.task,
            batch=args.batch,
            instance=args.instance,
            counter_of=args.counter_of,
            review_round=args.review_round,
        )
        if args.output:
            write_output(args.output, content)
        else:
            sys.stdout.write(content)
        return 0
    except (ContractError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
