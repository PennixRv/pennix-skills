#!/usr/bin/env python3
"""Verify and remove the exact pennix-skills collection installed by Codex."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import hashlib
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MANAGED_COMMANDS = {"grok-search": {"target": "grok-search/bin/grok-search", "link": ".local/bin/grok-search"}}


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
    if yaml is None:
        raise InstallError("Skill admission requires PyYAML; install the host's python-yaml package")
    skill_md = skill_directory / "SKILL.md"
    if not skill_md.is_file() or skill_md.is_symlink():
        raise InstallError(f"Missing safe SKILL.md: {skill_directory}")
    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise InstallError(f"Cannot safely read Skill: {skill_md}") from error
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
    if not frontmatter:
        raise InstallError(f"Invalid YAML frontmatter: {skill_md}")
    class UniqueSafeLoader(yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            self.flatten_mapping(node)
            mapping = {}
            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    if key in mapping:
                        raise yaml.constructor.ConstructorError(None, None, f"duplicate key: {key}", key_node.start_mark)
                    mapping[key] = self.construct_object(value_node, deep=deep)
                except TypeError as error:
                    raise yaml.constructor.ConstructorError(None, None, "unhashable key", key_node.start_mark) from error
            return mapping

    try:
        metadata = yaml.load(frontmatter.group(1), Loader=UniqueSafeLoader)
    except yaml.YAMLError as error:
        raise InstallError(f"Invalid YAML frontmatter: {skill_md}: {error}") from error
    if not isinstance(metadata, dict):
        raise InstallError(f"Skill frontmatter must be a mapping: {skill_md}")
    name, description = metadata.get("name"), metadata.get("description")
    if not isinstance(name, str) or len(name) > 64 or not SKILL_NAME.fullmatch(name):
        raise InstallError(f"Missing valid Skill name: {skill_md}")
    if name != skill_directory.name:
        raise InstallError(f"Skill name does not match directory: {skill_md}")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise InstallError(f"Missing valid Skill description: {skill_md}")
    return name


def format_readiness() -> dict[str, str]:
    return {"status": "ready" if yaml is not None else "missing", "parser": "PyYAML"}


def collection_state(expected_names: set[str], destination: Path, bootstrap_name: str | None = None) -> str:
    if yaml is None:
        raise InstallError("Skill admission requires PyYAML; install the host's python-yaml package")
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
    if hasattr(os, "getuid") and path.stat().st_uid != os.getuid():
        raise InstallError("collection integrity receipt owner is unsafe")


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


def collection_receipt(destination: Path) -> dict | None:
    receipt = receipt_path(destination)
    if not receipt.exists() and not receipt.is_symlink():
        return None
    try:
        _assert_private_regular(receipt)
        value = json.loads(receipt.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("destination") != destination.name:
            return None
        if not isinstance(value.get("digest"), str) or not re.fullmatch(r"[0-9a-f]{64}", value["digest"]):
            return None
        if value.get("schema") == 1 and set(value) == {"schema", "destination", "digest"}:
            return value if value["digest"] == collection_digest(destination) else None
        if value.get("schema") == 2 and set(value) == {"schema", "destination", "digest", "commands"}:
            return value
        return None
    except (InstallError, OSError, json.JSONDecodeError):
        return None


def collection_receipt_state(destination: Path, expected_commands: dict | None = None) -> str:
    value = collection_receipt(destination)
    if value is None:
        receipt = receipt_path(destination)
        return "drifted" if receipt.exists() or receipt.is_symlink() else "legacy"
    if value.get("schema") == 1:
        return "legacy" if not value.get("commands") else "drifted"
    commands = value.get("commands")
    if (
        value.get("schema") != 2
        or value.get("destination") != destination.name
        or not isinstance(value.get("digest"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", value["digest"])
        or not isinstance(commands, dict)
        or commands not in ({}, MANAGED_COMMANDS)
        or (expected_commands is not None and commands != expected_commands)
    ):
        return "drifted"
    try:
        return "match" if value["digest"] == collection_digest(destination) else "drifted"
    except (InstallError, OSError):
        return "drifted"


def _write_receipt(destination: Path, digest: str, commands: dict | None = None) -> Path:
    receipt = receipt_path(destination)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{receipt.name}.", dir=receipt.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        temporary.write_text(
            json.dumps({"schema": 2, "destination": destination.name, "digest": digest, "commands": commands or {}}, sort_keys=True) + "\n",
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
    obsolete_names: set[str] | None = None,
    commands: dict | None = None,
    command_home: Path | None = None,
) -> None:
    """Replace a known collection only after the complete staged tree validates."""
    staging = validate_staged_collection(expected_names, staging)
    destination = assert_safe_destination(destination)
    if staging.parent != destination.parent:
        raise InstallError("staging and destination must share a parent for transactional replacement")
    current_state = collection_state(expected_names, destination, bootstrap_name)
    # A catalog may remove entries. The existing private integrity receipt,
    # not a hard-coded retired-product list, proves the managed prior tree.
    if current_state == "drifted" and collection_receipt_state(destination) == "match":
        entries = {entry.name for entry in destination.iterdir()}
        try:
            valid_prior = bool(entries) and all(
                SKILL_NAME.fullmatch(name) and read_skill_name(destination / name) == name
                for name in entries
            )
        except (InstallError, OSError):
            valid_prior = False
        if valid_prior:
            current_state = "obsolete"
    obsolete_names = obsolete_names or set()
    if current_state == "drifted" and obsolete_names and destination.exists():
        entries = {entry.name for entry in destination.iterdir()}
        if entries <= expected_names | obsolete_names:
            try:
                obsolete_valid = all(
                    name not in obsolete_names or read_skill_name(destination / name) == name for name in entries
                )
            except (InstallError, OSError):
                obsolete_valid = False
            if obsolete_valid and entries & obsolete_names:
                current_state = "obsolete"
    if current_state not in {"missing", "bootstrap", "partial", "match", "obsolete"}:
        raise InstallError("refusing to replace a drifted or unknown Pennix Skills collection")
    integrity = collection_receipt_state(destination)
    if current_state == "match" and (integrity == "drifted" or (integrity == "legacy" and not allow_legacy)):
        raise InstallError("refusing to replace a legacy or drifted Pennix Skills collection")
    if staging == destination:
        return

    commands = commands or {}
    if commands not in ({}, MANAGED_COMMANDS):
        raise InstallError("managed command map is invalid")
    command_links: list[tuple[Path, Path]] = []
    if commands:
        home = command_home or Path.home()
        bin_directory = home / ".local" / "bin"
        for name, mapping in commands.items():
            staged_target = staging / mapping["target"]
            target = destination / mapping["target"]
            link = home / mapping["link"]
            if not staged_target.is_file() or staged_target.is_symlink() or not (staged_target.stat().st_mode & 0o111):
                raise InstallError(f"managed command target is not a regular executable: {name}")
            _assert_no_symlink_path(bin_directory)
            if link.parent.exists() and (not link.parent.is_dir() or link.parent.stat().st_mode & 0o022):
                raise InstallError("managed command directory is unsafe")
            resolved_command = shutil.which(name)
            if resolved_command and Path(resolved_command).absolute() != link.absolute():
                raise InstallError(f"managed command is shadowed on PATH: {name}")
            if link.exists() or link.is_symlink():
                if not link.is_symlink():
                    raise InstallError(f"refusing to adopt an unmanaged command path: {mapping['link']}")
                receipt = collection_receipt(destination)
                try:
                    actual = link.resolve(strict=True)
                    expected = target.resolve(strict=True)
                except OSError as error:
                    raise InstallError("managed command link is unsafe") from error
                if (
                    actual != expected
                    or not isinstance(receipt, dict)
                    or receipt.get("schema") != 2
                    or receipt.get("commands") != commands
                    or collection_receipt_state(destination, commands) != "match"
                ):
                    raise InstallError(f"refusing to adopt an unmanaged command path: {mapping['link']}")
            else:
                command_links.append((link, target))

    staged_receipt = _write_receipt(destination, collection_digest(staging), commands)

    backup: Path | None = None
    receipt_backup: Path | None = None
    installed_links: list[Path] = []
    receipt = receipt_path(destination)
    installed = False
    receipt_installed = False
    created_directories: list[Path] = []
    try:
        for link, _ in command_links:
            missing = []
            parent = link.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir(mode=0o755)
                created_directories.append(directory)
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
        installed = True
        os.replace(staged_receipt, receipt)
        receipt_installed = True
        for link, target in command_links:
            link.symlink_to(target)
            installed_links.append(link)
    except OSError:
        for link in installed_links:
            link.unlink(missing_ok=True)
        if receipt_installed:
            receipt.unlink(missing_ok=True)
        if installed:
            os.replace(destination, staging)
        if backup is not None and not destination.exists():
            os.replace(backup, destination)
        if receipt_backup is not None and not receipt.exists():
            os.replace(receipt_backup, receipt)
        for directory in reversed(created_directories):
            directory.rmdir()
        raise
    finally:
        staged_receipt.unlink(missing_ok=True)
    if backup is not None:
        shutil.rmtree(backup)
    if receipt_backup is not None:
        receipt_backup.unlink(missing_ok=True)


def _assert_no_symlink_path(path: Path) -> None:
    current = path.absolute()
    while current != current.parent:
        if current.is_symlink():
            raise InstallError("managed command directory traverses a symbolic link")
        current = current.parent


def uninstall_collection(
    expected_names: set[str], destination: Path, bootstrap_name: str | None = None,
    commands: dict | None = None, command_home: Path | None = None,
) -> bool:
    state = collection_state(expected_names, destination, bootstrap_name)
    if state == "missing":
        return False
    if state not in {"match", "bootstrap"}:
        raise InstallError("refusing to remove a non-exact Pennix Skills collection")
    commands = commands or {}
    if state == "match" and collection_receipt_state(destination, commands) != "match":
        raise InstallError("refusing to remove a legacy or drifted Pennix Skills collection")
    for mapping in commands.values():
        link = (command_home or Path.home()) / mapping["link"]
        _assert_no_symlink_path(link.parent)
        if state == "match" and not link.is_symlink():
            raise InstallError("managed command link is missing or drifted")
    removed_links: list[tuple[Path, str]] = []
    collection_backup: Path | None = None
    receipt_backup: Path | None = None
    receipt = receipt_path(destination)
    try:
        for mapping in commands.values():
            link = (command_home or Path.home()) / mapping["link"]
            if link.exists() or link.is_symlink():
                if state != "match":
                    raise InstallError(f"refusing to remove an unowned command path: {mapping['link']}")
                if not link.is_symlink() or link.resolve(strict=True) != (destination / mapping["target"]).resolve(strict=True):
                    raise InstallError(f"refusing to remove an unowned command path: {mapping['link']}")
                target_text = os.readlink(link)
                link.unlink()
                removed_links.append((link, target_text))
        collection_backup = Path(tempfile.mkdtemp(prefix=f".{destination.name}.uninstall-", dir=destination.parent))
        collection_backup.rmdir()
        os.replace(destination, collection_backup)
        if receipt.exists():
            descriptor, backup_name = tempfile.mkstemp(prefix=f".{receipt.name}.uninstall-", dir=receipt.parent)
            os.close(descriptor)
            receipt_backup = Path(backup_name)
            receipt_backup.unlink()
            os.replace(receipt, receipt_backup)
    except (OSError, InstallError):
        if receipt_backup is not None and receipt_backup.exists() and not receipt.exists():
            os.replace(receipt_backup, receipt)
        if collection_backup is not None and collection_backup.exists() and not destination.exists():
            os.replace(collection_backup, destination)
        for link, target_text in removed_links:
            if not link.exists() and not link.is_symlink():
                link.symlink_to(target_text)
        raise
    if collection_backup is not None:
        shutil.rmtree(collection_backup)
    if receipt_backup is not None:
        receipt_backup.unlink(missing_ok=True)
    return True
