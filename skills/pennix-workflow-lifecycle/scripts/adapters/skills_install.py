#!/usr/bin/env python3
"""Verify and remove the exact Pennix Skills collection installed by Codex."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class InstallError(RuntimeError):
    """Raised when the managed collection cannot be identified safely."""


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def default_destination() -> Path:
    return codex_home() / "skills" / "pennix-skills"


def assert_safe_destination(destination: Path) -> Path:
    destination = destination.absolute()
    current = destination
    while True:
        if current.is_symlink():
            raise InstallError(f"Destination must not traverse a symbolic link: {current}")
        if current == current.parent:
            break
        current = current.parent
    if destination.exists() and not destination.is_dir():
        raise InstallError(f"Destination must be a directory: {destination}")
    return destination


def resolve_destination(raw_destination: str | None) -> Path:
    destination = Path(raw_destination).expanduser() if raw_destination else default_destination()
    destination = assert_safe_destination(destination)
    if destination.name != "pennix-skills" or destination.parent.name != "skills":
        raise InstallError(
            "Destination must be a pennix-skills directory directly under a skills directory"
        )
    return destination


def read_skill_name(skill_directory: Path) -> str:
    skill_md = skill_directory / "SKILL.md"
    if not skill_md.is_file() or skill_md.is_symlink():
        raise InstallError(f"Missing safe SKILL.md: {skill_directory}")
    content = skill_md.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
    if not frontmatter:
        raise InstallError(f"Invalid YAML frontmatter: {skill_md}")
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter.group(1), re.MULTILINE)
    if not match:
        raise InstallError(f"Missing valid Skill name: {skill_md}")
    return match.group(1)


def collection_state(expected_names: set[str], destination: Path, bootstrap_name: str | None = None) -> str:
    destination = assert_safe_destination(destination)
    if not destination.exists():
        return "missing"
    entries = {entry.name for entry in destination.iterdir()}
    if bootstrap_name is not None and entries == {bootstrap_name}:
        try:
            return "bootstrap" if read_skill_name(destination / bootstrap_name) == bootstrap_name else "drifted"
        except (InstallError, OSError):
            return "drifted"
    if not entries <= expected_names:
        return "drifted"
    for name in entries:
        skill_directory = destination / name
        if skill_directory.is_symlink() or not skill_directory.is_dir():
            return "drifted"
        try:
            if read_skill_name(skill_directory) != name:
                return "drifted"
        except (InstallError, OSError):
            return "drifted"
    return "match" if entries == expected_names else "partial"


def collection_missing_names(expected_names: set[str], destination: Path, bootstrap_name: str | None = None) -> list[str] | None:
    state = collection_state(expected_names, destination, bootstrap_name)
    if state not in {"bootstrap", "partial", "match"}:
        return None
    return sorted(expected_names - {entry.name for entry in destination.iterdir()})


def uninstall_collection(expected_names: set[str], destination: Path, bootstrap_name: str | None = None) -> bool:
    state = collection_state(expected_names, destination, bootstrap_name)
    if state == "missing":
        return False
    if state not in {"match", "bootstrap"}:
        raise InstallError("refusing to remove a non-exact Pennix Skills collection")
    shutil.rmtree(destination)
    return True
