#!/usr/bin/env python3
"""Launch native Codex with Cognee enabled only for a registered project."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import stat
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from cognee_client import CogneeClient, CogneeError


# Native -c splits on dots; quoting a segment creates a different literal key.
PLUGIN = 'plugins.cognee@cognee.enabled'
DATASET_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _private_values(path: Path) -> dict[str, str] | None:
    try:
        if any(parent.is_symlink() for parent in path.absolute().parents):
            return None
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            return None
        values = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.removeprefix("export ").split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
        return values
    except (OSError, UnicodeError):
        return None


def _registered_dataset(home: Path, cwd: Path) -> str | None:
    config = _private_values(home / ".cognee" / ".env")
    if not config or config.get("COGNEE_MANAGED_ENDPOINT", "").lower() != "true":
        return None
    if config.get("COGNEE_SHARED_AGENT_MEMORY", "").lower() != "false":
        return None
    try:
        return CogneeClient.for_project(cwd).project
    except CogneeError as error:
        print(f"Pennix launcher: memory disabled ({error})", file=sys.stderr)
        return None


def _launch_root(arguments: list[str]) -> Path | None:
    # A resumed/forked host needs its own verified binding, not the current cwd.
    if any(value in {"resume", "fork"} for value in arguments):
        return None
    root = Path.cwd()
    for index, value in enumerate(arguments):
        if value in {"--cd", "-C"}:
            if index + 1 == len(arguments):
                return None
            root = Path(arguments[index + 1]).expanduser()
        elif value.startswith("--cd="):
            root = Path(value.split("=", 1)[1]).expanduser()
    return root.resolve() if root.is_dir() else None


def main(argv: list[str] | None = None) -> int:
    codex = shutil.which("codex")
    if codex is None:
        print("Pennix launcher: native Codex CLI is unavailable", file=sys.stderr)
        return 127
    arguments = sys.argv[1:] if argv is None else argv
    root = _launch_root(arguments)
    dataset = _registered_dataset(Path.home(), root) if root is not None else None
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith("COGNEE_"):
            env.pop(key, None)
    if dataset:
        env["COGNEE_PLUGIN_DATASET"] = dataset
        env["COGNEE_PLUGIN_IDENTITY"] = "false"
    setting = f"{PLUGIN}={'true' if dataset else 'false'}"
    os.execvpe(codex, [codex, "--no-daemon", "-c", setting, *arguments], env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
