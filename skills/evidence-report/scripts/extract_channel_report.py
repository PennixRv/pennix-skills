#!/usr/bin/env python3
"""Extract exactly one wrapped candidate report from a Trellis channel event log."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import ContractError, SECRET_RE, write_json_file  # noqa: E402


MAX_EVENTS_BYTES = 8 * 1024 * 1024
WRAPPED_REPORT = re.compile(
    r"\A<CANDIDATE_REPORT>\s*(\{.*\})\s*</CANDIDATE_REPORT>\s*\Z",
    re.DOTALL,
)


def load_events(path: Path) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise ContractError("channel events must be a regular file")
    if path.stat().st_size > MAX_EVENTS_BYTES:
        raise ContractError("channel events exceed %d bytes" % MAX_EVENTS_BYTES)
    events: list[dict[str, Any]] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ContractError("channel event %d is not an object" % line_number)
            events.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("channel events are unreadable or invalid") from exc
    return events


def extract(events: list[dict[str, Any]], worker: str, after_seq: int) -> dict[str, Any]:
    if after_seq < 0:
        raise ContractError("after_seq must not be negative")
    candidates: list[dict[str, Any]] = []
    for event in events:
        sequence = event.get("seq")
        if not isinstance(sequence, int) or sequence <= after_seq:
            continue
        if event.get("kind") != "say" or event.get("by") != worker:
            continue
        text = event.get("text")
        if not isinstance(text, str):
            continue
        matched = WRAPPED_REPORT.fullmatch(text)
        if not matched:
            continue
        try:
            payload = json.loads(matched.group(1))
        except json.JSONDecodeError as exc:
            raise ContractError("candidate report wrapper contains invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ContractError("candidate report wrapper must contain an object")
        if SECRET_RE.search(json.dumps(payload, ensure_ascii=False)):
            raise ContractError("candidate report wrapper contains a possible credential or secret")
        candidates.append(payload)
    if len(candidates) != 1:
        raise ContractError("expected exactly one candidate report after the send sequence; found %d" % len(candidates))
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--worker", required=True)
    parser.add_argument("--after-seq", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        write_json_file(args.output, extract(load_events(args.events), args.worker, args.after_seq))
        return 0
    except (ContractError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
