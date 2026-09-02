#!/usr/bin/env python3
"""Initialize a Trellis project through one explicit, non-interactive mode."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable


DEFAULT_DEVELOPER = "penn"


class InitializationError(RuntimeError):
    """Report a safe, bounded initialization failure."""


Runner = Callable[..., subprocess.CompletedProcess[str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", required=True, choices=("trellis-only",))
    parser.add_argument("--developer", default=DEFAULT_DEVELOPER)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_project_root(raw_value: str) -> Path:
    raw = Path(raw_value)
    if not raw.is_absolute():
        raise InitializationError("project_root_must_be_absolute")
    if raw.is_symlink() or not raw.exists() or not raw.is_dir():
        raise InitializationError("project_root_must_be_existing_regular_directory")
    root = raw.resolve(strict=True)
    prohibited = {
        Path("/").resolve(),
        Path.home().resolve(),
        (Path.home() / ".codex").resolve(),
        (Path.home() / ".agents").resolve(),
    }
    if root in prohibited:
        raise InitializationError("project_root_is_global_or_broad_directory")
    return root


def run_checked(command: list[str], root: Path, runner: Runner, operation: str) -> str:
    result = runner(
        command,
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise InitializationError(f"command_failed:{operation}:{result.returncode}")
    return result.stdout


def run_initialization(
    *,
    root: Path,
    mode: str,
    developer: str,
    dry_run: bool,
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    if mode != "trellis-only":
        raise InitializationError("unsupported_initialization_mode")
    summary: dict[str, object] = {
        "status": "planned" if dry_run else "initialized",
        "project_root": str(root),
        "mode": mode,
        "developer": developer,
        "dry_run": dry_run,
        "trellis": "would_run" if dry_run else "pending",
    }
    if dry_run:
        return summary

    run_checked(
        [
            "trellis",
            "init",
            "--yes",
            "--codex",
            "--workflow",
            "channel-driven-subagent-dispatch",
            "--skip-existing",
            "-u",
            developer,
        ],
        root,
        runner,
        "trellis-init",
    )
    summary["trellis"] = "initialized_or_preserved"
    return summary


def main() -> int:
    args = parse_args()
    try:
        root = resolve_project_root(args.project_root)
        result = run_initialization(
            root=root,
            mode=args.mode,
            developer=args.developer,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    except InitializationError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=True, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
