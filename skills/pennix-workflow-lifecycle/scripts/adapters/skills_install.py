#!/usr/bin/env python3
"""Install the complete Pennix Skills collection from a local checkout."""

from __future__ import annotations

import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INSTALLABLE_ENTRIES = {
    "SKILL.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "UPSTREAM.md",
    "package.json",
    "package-lock.json",
    "agents",
    "assets",
    "bin",
    "references",
    "scripts",
    "templates",
}


class InstallError(RuntimeError):
    """Raised when the collection cannot be installed safely."""


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def default_destination() -> Path:
    return codex_home() / "skills" / "pennix-skills"


def run_git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise InstallError(f"Git command failed: {detail}")
    return result.stdout


def resolve_source(raw_source: str) -> Path:
    source = Path(raw_source).expanduser().resolve()
    if not source.is_dir():
        raise InstallError(f"Source checkout does not exist: {source}")

    repository_root = Path(run_git(source, "rev-parse", "--show-toplevel").strip()).resolve()
    if repository_root != source:
        raise InstallError(f"--source must be the pennix-skills repository root: {repository_root}")
    if not (source / "skills").is_dir():
        raise InstallError(f"Source checkout has no skills directory: {source}")
    if run_git(source, "status", "--porcelain").strip():
        raise InstallError("Source checkout has uncommitted changes")
    return source


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


def ensure_submodules(
    source: Path, initialize: bool, expected_commits: dict[str, str] | None = None
) -> None:
    if initialize:
        run_git(source, "submodule", "update", "--init", "--recursive")

    status_lines = run_git(source, "submodule", "status", "--recursive").splitlines()
    unresolved = [line for line in status_lines if line and line[0] in {"-", "+", "U"}]
    if unresolved:
        joined = "; ".join(unresolved)
        raise InstallError(f"Submodule checkout is not pinned and ready: {joined}")

    observed_commits: dict[str, str] = {}
    for line in status_lines:
        fields = line[1:].strip().split(maxsplit=2)
        if len(fields) < 2:
            raise InstallError(f"Unable to resolve submodule path: {line}")
        observed_commits[fields[1]] = fields[0]
        if expected_commits is not None and expected_commits.get(fields[1]) != fields[0]:
            raise InstallError(f"Submodule commit does not match catalog: {fields[1]}")
        submodule = source / fields[1]
        if run_git(submodule, "status", "--porcelain").strip():
            raise InstallError(f"Submodule checkout has uncommitted changes: {fields[1]}")
    if expected_commits is not None:
        missing = sorted(set(expected_commits) - set(observed_commits))
        if missing:
            raise InstallError(f"Catalog submodule is missing: {', '.join(missing)}")


def read_skill_name(skill_directory: Path) -> str:
    skill_md = skill_directory / "SKILL.md"
    if not skill_md.is_file():
        raise InstallError(f"Missing SKILL.md: {skill_directory}")

    content = skill_md.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
    if not frontmatter:
        raise InstallError(f"Invalid YAML frontmatter: {skill_md}")

    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter.group(1), re.MULTILINE)
    if not match:
        raise InstallError(f"Missing valid Skill name: {skill_md}")
    return match.group(1)


def discover_skills(source: Path) -> list[tuple[str, Path]]:
    skills_root = source / "skills"
    skills: list[tuple[str, Path]] = []
    for skill_directory in sorted(skills_root.iterdir(), key=lambda item: item.name):
        if not skill_directory.is_dir() or skill_directory.name.startswith("."):
            continue
        if not SKILL_NAME.fullmatch(skill_directory.name):
            raise InstallError(f"Invalid Skill directory name: {skill_directory.name}")
        skill_name = read_skill_name(skill_directory)
        if skill_name != skill_directory.name:
            raise InstallError(
                f"Skill directory and frontmatter name differ: {skill_directory.name} != {skill_name}"
            )
        skills.append((skill_name, skill_directory))
    if not skills:
        raise InstallError(f"No direct Skills found in: {skills_root}")
    return skills


def copy_skill(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        if path.is_symlink():
            raise InstallError(f"Skill source contains a symbolic link: {path}")

    destination.mkdir(parents=True)
    for entry in INSTALLABLE_ENTRIES:
        source_entry = source / entry
        if not source_entry.exists():
            continue
        target_entry = destination / entry
        if source_entry.is_dir():
            shutil.copytree(source_entry, target_entry, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(source_entry, target_entry)


def install_grok_search_dependency(stage: Path) -> None:
    package = stage / "grok-search"
    if not package.is_dir():
        return

    try:
        result = subprocess.run(
            ["npm", "ci", "--omit=dev", "--ignore-scripts"],
            cwd=package,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise InstallError("grok-search requires npm on the target host") from error

    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown npm error"
        raise InstallError(f"Unable to install grok-search dependencies: {detail}")


def same_tree(left: Path, right: Path) -> bool:
    if left.is_symlink() or right.is_symlink():
        return False
    if left.is_dir() != right.is_dir():
        return False
    if not left.is_dir():
        return filecmp.cmp(left, right, shallow=False)
    left_entries = {entry.name: entry for entry in left.iterdir()}
    right_entries = {entry.name: entry for entry in right.iterdir()}
    if left_entries.keys() != right_entries.keys():
        return False
    return all(
        same_tree(left_entries[name], right_entries[name])
        for name in left_entries
    )


def install_skills(skills: list[tuple[str, Path]], destination: Path) -> bool:
    destination = assert_safe_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".pennix-skills-stage-", dir=destination.parent))
    backup: Path | None = None
    try:
        for skill_name, skill_source in skills:
            copy_skill(skill_source, stage / skill_name)
        install_grok_search_dependency(stage)

        if destination.exists() and same_tree(stage, destination):
            return False
        if destination.exists():
            backup = destination.parent / f".pennix-skills-backup-{uuid.uuid4().hex}"
            os.replace(destination, backup)
        try:
            os.replace(stage, destination)
        except OSError:
            if backup is not None and backup.exists():
                os.replace(backup, destination)
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return True
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def uninstall_skills(skills: list[tuple[str, Path]], destination: Path) -> None:
    destination = assert_safe_destination(destination)
    if not destination.exists():
        return
    if not destination.is_dir():
        raise InstallError(f"Destination must be a directory: {destination}")
    expected = {name for name, _ in skills}
    entries = {entry.name for entry in destination.iterdir()}
    if entries != expected or any((destination / name).is_symlink() or not (destination / name).is_dir() for name in expected):
        raise InstallError("refusing to remove a non-exact Pennix Skills collection")
    shutil.rmtree(destination)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Path to the pennix-skills checkout")
    parser.add_argument(
        "--dest",
        help=(
            "selected host Skill discovery destination; must be a "
            "pennix-skills directory under a skills directory "
            "(defaults to $CODEX_HOME/skills/pennix-skills)"
        ),
    )
    parser.add_argument("--check", action="store_true", help="Validate source and submodules without installing")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        source = resolve_source(args.source)
        destination = resolve_destination(args.dest)
        ensure_submodules(source, initialize=not args.check)
        skills = discover_skills(source)
        if args.check:
            print(f"Validated {len(skills)} Pennix Skills from {source}")
            return 0
        install_skills(skills, destination)
        print(f"Installed {len(skills)} Pennix Skills to {destination}")
        return 0
    except InstallError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
