#!/usr/bin/env python3
"""Validate and emit a Trellis candidate-work request; never starts a worker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_contracts import (  # noqa: E402
    ContractError,
    load_json_file,
    normalize_candidate_request,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        value = load_json_file(args.input, 64 * 1024)
        result = normalize_candidate_request(value)
        encoded = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
        if args.output:
            write_output(args.output, encoded)
        else:
            sys.stdout.write(encoded)
        return 0
    except (ContractError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
