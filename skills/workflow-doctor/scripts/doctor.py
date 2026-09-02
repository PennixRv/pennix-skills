#!/usr/bin/env python3
"""Read-only diagnostics for the Trellis fork and project Skill layer."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict


def check(path: Path, kind: str = "file") -> Dict[str, Any]:
    present = path.is_file() if kind == "file" else path.is_dir()
    return {"path": str(path), "status": "pass" if present else "missing"}


def git_state(path: Path) -> Dict[str, Any]:
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--short", "--branch"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode:
        return {"status": "unavailable"}
    lines = result.stdout.splitlines()
    return {"status": "pass", "branch": lines[0] if lines else "", "dirty": max(len(lines) - 1, 0)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    checks = [
        check(root / ".trellis", "dir"),
        check(root / "AGENTS.md"),
        check(root / ".trellis/workflow.md"),
        check(root / ".trellis/scripts/task.py"),
        check(root / ".agents/skills", "dir"),
        check(root / "Trellis/package.json"),
    ]
    trellis_state = git_state(root / "Trellis") if (root / "Trellis").is_dir() else {"status": "missing"}
    package_scope = "unknown"
    package_file = root / "Trellis/packages/cli/package.json"
    if package_file.is_file():
        try:
            package_scope = json.loads(package_file.read_text(encoding="utf-8")).get("name", "unknown")
        except (OSError, json.JSONDecodeError):
            package_scope = "invalid"
    legacy_profile = root / ".trellis/codex-workflow.json"
    stale_paths = [legacy_profile.relative_to(root).as_posix()] if legacy_profile.is_file() else []
    status = "pass" if all(item["status"] == "pass" for item in checks) and trellis_state["status"] == "pass" else "degraded"
    output = {
        "status": status,
        "project_root": str(root),
        "checks": checks,
        "trellis": trellis_state,
        "package_scope": package_scope,
        "stale_workflow_paths": stale_paths,
        "mutated": False,
    }
    print(json.dumps(output, ensure_ascii=True, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
