"""Thin wrapper for the native Trellis CLI; no lifecycle is copied here."""

from __future__ import annotations

import shutil
import subprocess


def version() -> str | None:
    command = shutil.which("trellis")
    if not command:
        return None
    result = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=10, check=False)
    if result.returncode:
        return None
    return (result.stdout or result.stderr).strip().splitlines()[0] or None
