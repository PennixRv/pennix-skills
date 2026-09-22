#!/usr/bin/env python3
"""Verify and remove the exact Pennix Skills collection installed by Codex."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import hashlib
import json
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


def receipt_path(destination: Path) -> Path:
    return destination.parent / f".{destination.name}.receipt.json"


def _assert_private_regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file() or (path.stat().st_mode & 0o077) != 0:
        raise InstallError("collection integrity receipt is unsafe")


def collection_digest(destination: Path) -> str:
    """Digest a safe managed tree without treating arbitrary entries as content."""
    destination = assert_safe_destination(destination)
    digest = hashlib.sha256()
    paths = (
        path
        for path in destination.rglob("*")
        if "__pycache__" not in path.relative_to(destination).parts
    )
    for path in sorted(paths, key=lambda candidate: candidate.relative_to(destination).as_posix()):
        relative = path.relative_to(destination).as_posix()
        # Python bytecode is regenerable runtime cache, not managed collection content.
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise InstallError(f"collection contains a symbolic link: {relative}")
        if path.is_dir():
            digest.update(f"D\0{relative}\0".encode())
            continue
        if not path.is_file():
            raise InstallError(f"collection contains a non-regular entry: {relative}")
        mode = path.stat().st_mode & 0o111
        digest.update(f"F\0{relative}\0{mode:o}\0".encode())
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def collection_receipt_state(destination: Path) -> str:
    receipt = receipt_path(destination)
    if not receipt.exists():
        return "legacy"
    try:
        _assert_private_regular(receipt)
        value = json.loads(receipt.read_text(encoding="utf-8"))
        if (
            not isinstance(value, dict)
            or value.get("schema") != 1
            or value.get("destination") != destination.name
            or not isinstance(value.get("digest"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["digest"])
        ):
            return "drifted"
        return "match" if value["digest"] == collection_digest(destination) else "drifted"
    except (InstallError, OSError, json.JSONDecodeError):
        return "drifted"


def _write_receipt(destination: Path, digest: str) -> Path:
    receipt = receipt_path(destination)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{receipt.name}.", dir=receipt.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        temporary.write_text(
            json.dumps({"schema": 1, "destination": destination.name, "digest": digest}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def validate_staged_collection(expected_names: set[str], staging: Path) -> Path:
    """Validate a native-installer staging tree before it can replace a collection."""
    staging = assert_safe_destination(staging)
    if collection_state(expected_names, staging) != "match":
        raise InstallError("native installer staging is not an exact Pennix Skills collection")
    return staging


def replace_collection(
    expected_names: set[str],
    staging: Path,
    destination: Path,
    bootstrap_name: str | None = None,
    allow_legacy: bool = False,
) -> None:
    """Replace a known collection only after the complete staged tree validates."""
    staging = validate_staged_collection(expected_names, staging)
    destination = assert_safe_destination(destination)
    if staging.parent != destination.parent:
        raise InstallError("staging and destination must share a parent for transactional replacement")
    current_state = collection_state(expected_names, destination, bootstrap_name)
    if current_state not in {"missing", "bootstrap", "partial", "match"}:
        raise InstallError("refusing to replace a drifted or unknown Pennix Skills collection")
    if current_state == "match" and collection_receipt_state(destination) != "match" and not allow_legacy:
        raise InstallError("refusing to replace a legacy or drifted Pennix Skills collection")
    if staging == destination:
        return

    staged_receipt = _write_receipt(destination, collection_digest(staging))

    backup: Path | None = None
    receipt_backup: Path | None = None
    receipt = receipt_path(destination)
    try:
        if destination.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{destination.name}.previous-", dir=destination.parent))
            shutil.rmtree(backup)
            os.replace(destination, backup)
        if receipt.exists():
            descriptor, backup_name = tempfile.mkstemp(prefix=f".{receipt.name}.previous-", dir=destination.parent)
            os.close(descriptor)
            receipt_backup = Path(backup_name)
            receipt_backup.unlink()
            os.replace(receipt, receipt_backup)
        os.replace(staging, destination)
        os.replace(staged_receipt, receipt)
    except OSError:
        if backup is not None and not destination.exists():
            os.replace(backup, destination)
        if receipt_backup is not None and not receipt.exists():
            os.replace(receipt_backup, receipt)
        raise
    finally:
        staged_receipt.unlink(missing_ok=True)
    if backup is not None:
        shutil.rmtree(backup)
    if receipt_backup is not None:
        receipt_backup.unlink(missing_ok=True)


def uninstall_collection(expected_names: set[str], destination: Path, bootstrap_name: str | None = None) -> bool:
    state = collection_state(expected_names, destination, bootstrap_name)
    if state == "missing":
        return False
    if state not in {"match", "bootstrap"}:
        raise InstallError("refusing to remove a non-exact Pennix Skills collection")
    if state == "match" and collection_receipt_state(destination) != "match":
        raise InstallError("refusing to remove a legacy or drifted Pennix Skills collection")
    shutil.rmtree(destination)
    receipt_path(destination).unlink(missing_ok=True)
    return True
