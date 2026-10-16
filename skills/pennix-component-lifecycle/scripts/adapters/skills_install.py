#!/usr/bin/env python3
"""Validate and transactionally replace registered Skill collections."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import hashlib
import json
import stat
from pathlib import Path

from . import codex_static

try:
    import yaml
except ImportError:
    yaml = None


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COLLECTION_NAMES = {"pennix-skills", "pennix-skills-extra"}
MANAGED_COMMANDS = {
    "grok-search": {"target": "pennix-grok-search/bin/grok-search", "link": ".local/bin/grok-search"},
    "windsurf-code-search": {
        "target": "pennix-windsurf-code-search/bin/windsurf-code-search",
        "link": ".local/bin/windsurf-code-search",
    },
}
LEGACY_MANAGED_COMMANDS = {
    "grok-search": {"target": "grok-search/bin/grok-search", "link": ".local/bin/grok-search"},
}


class InstallError(RuntimeError):
    """Raised when the managed collection cannot be identified safely."""


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def default_destination(collection_name: str = "pennix-skills", target_codex_home: Path | None = None) -> Path:
    return (target_codex_home or codex_home()) / "skills" / collection_name


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


def resolve_destination(
    raw_destination: str | None, collection_name: str = "pennix-skills", target_codex_home: Path | None = None,
) -> Path:
    if collection_name not in COLLECTION_NAMES:
        raise InstallError("unknown Skill collection destination")
    if raw_destination is not None and collection_name != "pennix-skills":
        raise InstallError("managed extra collection does not accept --destination overrides")
    destination = Path(raw_destination).expanduser() if raw_destination else default_destination(collection_name, target_codex_home)
    destination = assert_safe_destination(destination)
    if destination.name != collection_name or destination.parent.name != "skills":
        raise InstallError(
            f"Destination must be a {collection_name} directory directly under a skills directory"
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


def valid_collection_source(source: object) -> bool:
    if not isinstance(source, dict) or set(source) != {"repo", "ref", "skills"}:
        return False
    names = source.get("skills")
    return (
        isinstance(source.get("repo"), str)
        and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repo"]) is not None
        and isinstance(source.get("ref"), str)
        and re.fullmatch(r"[0-9a-f]{40}", source["ref"]) is not None
        and isinstance(names, list)
        and bool(names)
        and all(isinstance(name, str) and len(name) <= 64 and SKILL_NAME.fullmatch(name) for name in names)
        and names == sorted(set(names))
    )


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
        if (
            destination.name == "pennix-skills-extra"
            and value.get("schema") == 3
            and type(value.get("schema")) is int
            and set(value) == {"schema", "destination", "digest", "commands", "source"}
            and value.get("commands") == {}
            and valid_collection_source(value.get("source"))
        ):
            return value
        return None
    except (InstallError, OSError, json.JSONDecodeError):
        return None


def collection_receipt_state(
    destination: Path, expected_commands: dict | None = None, expected_source: dict | None = None,
) -> str:
    value = collection_receipt(destination)
    if value is None:
        receipt = receipt_path(destination)
        return "drifted" if receipt.exists() or receipt.is_symlink() else "legacy"
    if value.get("schema") == 3:
        source = value["source"]
        if expected_commands or (
            expected_source is not None
            and (
                not valid_collection_source(expected_source)
                or source["repo"] != expected_source["repo"]
                or source["skills"] != expected_source["skills"]
            )
        ):
            return "drifted"
        try:
            if value["digest"] != collection_digest(destination):
                return "drifted"
            if expected_source is not None and source["ref"] != expected_source["ref"]:
                return "upgrade-available"
            return "match"
        except (InstallError, OSError):
            return "drifted"
    if expected_source is not None or destination.name == "pennix-skills-extra":
        return "drifted"
    if value.get("schema") == 1:
        return "legacy" if not value.get("commands") else "drifted"
    commands = value.get("commands")
    if (
        value.get("schema") != 2
        or value.get("destination") != destination.name
        or not isinstance(value.get("digest"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", value["digest"])
        or not isinstance(commands, dict)
        or not _is_known_command_map(commands)
    ):
        return "drifted"
    if expected_commands is not None and commands != expected_commands:
        return "legacy" if commands == LEGACY_MANAGED_COMMANDS else "drifted"
    try:
        if value["digest"] != collection_digest(destination):
            return "drifted"
        return "legacy" if commands == LEGACY_MANAGED_COMMANDS else "match"
    except (InstallError, OSError):
        return "drifted"


def _is_known_command_map(commands: dict) -> bool:
    if not commands:
        return True
    if not all(isinstance(name, str) and isinstance(mapping, dict) for name, mapping in commands.items()):
        return False
    return all(
        name in MANAGED_COMMANDS
        and mapping in (MANAGED_COMMANDS[name], LEGACY_MANAGED_COMMANDS.get(name))
        for name, mapping in commands.items()
    )


def _write_receipt(
    destination: Path, digest: str, commands: dict | None = None, source: dict | None = None,
) -> Path:
    value = {"schema": 2, "destination": destination.name, "digest": digest, "commands": commands or {}}
    if source is not None:
        if destination.name != "pennix-skills-extra" or commands or not valid_collection_source(source):
            raise InstallError("managed collection source identity is invalid")
        value.update(schema=3, source=source)
    receipt = receipt_path(destination)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{receipt.name}.", dir=receipt.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        temporary.write_text(
            json.dumps(value, sort_keys=True) + "\n",
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


def _staging_identity(metadata: os.stat_result) -> tuple:
    return (metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid,
            metadata.st_gid, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)


def _staging_snapshot(staging: Path) -> dict:
    digest = hashlib.sha256()
    entries = 0
    file_bytes = 0
    for path in [staging, *sorted(staging.rglob("*"))]:
        before = path.lstat()
        if before.st_uid != os.getuid():
            raise InstallError(f"staging entry owner is unsafe: {path}")
        if not (stat.S_ISDIR(before.st_mode) or stat.S_ISREG(before.st_mode)):
            raise InstallError(f"staging contains a symbolic link or non-regular entry: {path}")
        identity = _staging_identity(before)
        digest.update(json.dumps([path.relative_to(staging).as_posix(), identity]).encode())
        digest.update(b"\0")
        if stat.S_ISREG(before.st_mode):
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as handle:
                if _staging_identity(os.fstat(handle.fileno())) != identity:
                    raise InstallError("staging changed during preview")
                for chunk in iter(lambda: handle.read(64 * 1024), b""):
                    digest.update(chunk)
                if _staging_identity(os.fstat(handle.fileno())) != identity:
                    raise InstallError("staging changed during preview")
            file_bytes += before.st_size
        if _staging_identity(path.lstat()) != identity:
            raise InstallError("staging changed during preview")
        digest.update(b"\0")
        entries += 1
    return {"digest": digest.hexdigest(), "entries": entries - 1, "file_bytes": file_bytes}


def discard_staged_collection(
    expected_names: set[str], staging: Path, target_codex_home: Path,
    *, execute: bool = False, expected_digest: str | None = None,
) -> dict:
    """Preview or explicitly discard one safe, selected Pennix Skills staging tree."""
    try:
        staging = assert_safe_destination(staging)
        skills_root = assert_safe_destination(target_codex_home / "skills")
        if (staging.parent != skills_root or staging != staging.resolve(strict=True)
                or not re.fullmatch(r"\.pennix-skills-stage(?:-[A-Za-z0-9_-]+)?", staging.name)):
            raise InstallError("staging must be an exact Pennix Skills staging directory under the selected Codex home")
        snapshot = _staging_snapshot(staging)
        if collection_state(expected_names, staging) not in {"match", "partial"}:
            raise InstallError("staging is not a valid Pennix Skills collection or member subset")
        if _staging_snapshot(staging) != snapshot:
            raise InstallError("staging changed during preview")
        result = {"status": "candidate", "staging": str(staging), **snapshot,
                  "skills": sorted(entry.name for entry in staging.iterdir())}
        if not execute:
            return result
        if not expected_digest or expected_digest != snapshot["digest"]:
            raise InstallError("staging preview digest is missing or does not match; nothing deleted")
        if not shutil.rmtree.avoids_symlink_attacks:
            raise InstallError("host cannot safely delete a staging tree")
        parent = os.open(skills_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            # shortcut: validation and deletion are not a transaction; coordinate owners if concurrent writers are supported.
            if _staging_snapshot(staging) != snapshot:
                raise InstallError("staging changed before deletion; nothing deleted")
            shutil.rmtree(staging.name, dir_fd=parent)
        finally:
            os.close(parent)
        if staging.exists() or staging.is_symlink():
            raise InstallError("staging deletion postcondition failed; inspect the remaining target")
        return {**result, "status": "executed", "deleted_file_bytes": snapshot["file_bytes"]}
    except OSError as error:
        raise InstallError(f"staging operation failed; inspect the remaining target {staging}: {error}") from error


def replace_collection(
    expected_names: set[str],
    staging: Path,
    destination: Path,
    bootstrap_name: str | None = None,
    allow_legacy: bool = False,
    obsolete_names: set[str] | None = None,
    commands: dict | None = None,
    command_home: Path | None = None,
    siyuan_config_update: tuple[Path, str, str] | None = None,
    source: dict | None = None,
) -> None:
    """Replace a known collection only after the complete staged tree validates."""
    staging = validate_staged_collection(expected_names, staging)
    destination = assert_safe_destination(destination)
    if staging.parent != destination.parent:
        raise InstallError("staging and destination must share a parent for transactional replacement")
    current_state = collection_state(expected_names, destination, bootstrap_name)
    if destination.name == "pennix-skills-extra" or source is not None:
        if (
            destination.name != "pennix-skills-extra"
            or not valid_collection_source(source)
            or source["skills"] != sorted(expected_names)
            or bootstrap_name is not None or allow_legacy or obsolete_names or commands or siyuan_config_update is not None
        ):
            raise InstallError("managed collection source identity is invalid")
        if current_state == "missing":
            receipt = receipt_path(destination)
            if receipt.exists() or receipt.is_symlink():
                raise InstallError("refusing an orphaned managed collection receipt")
        elif current_state != "match" or collection_receipt_state(destination, {}, source) not in {"match", "upgrade-available"}:
            raise InstallError("refusing an unknown or drifted managed collection")
    # A catalog may remove entries. The existing private integrity receipt,
    # not a hard-coded retired-product list, proves the managed prior tree.
    prior = collection_receipt(destination)
    prior_state = collection_receipt_state(destination)
    legacy_owned = (
        isinstance(prior, dict)
        and prior.get("schema") == 2
        and prior.get("commands") == LEGACY_MANAGED_COMMANDS
        and prior_state == "legacy"
    )
    if current_state == "drifted" and (prior_state == "match" or legacy_owned):
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

    if siyuan_config_update is not None:
        path, before, _ = siyuan_config_update
        if codex_static.read(path) != before:
            raise InstallError("SiYuan config changed concurrently")

    commands = commands or {}
    if not _is_known_command_map(commands):
        raise InstallError("managed command map is invalid")
    command_links: list[tuple[Path, Path]] = []
    prior_receipt = collection_receipt(destination)
    prior_commands = prior_receipt.get("commands") if isinstance(prior_receipt, dict) else None
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
                try:
                    actual = link.resolve(strict=True)
                    expected = target.resolve(strict=False)
                except OSError as error:
                    raise InstallError("managed command link is unsafe") from error
                current_owned = (
                    isinstance(prior_receipt, dict)
                    and prior_receipt.get("schema") == 2
                    and prior_commands in (commands, LEGACY_MANAGED_COMMANDS)
                    and collection_receipt_state(destination) in {"match", "legacy"}
                )
                legacy_target = destination / LEGACY_MANAGED_COMMANDS.get(name, {}).get("target", "")
                if not current_owned or (actual != expected and actual != legacy_target):
                    raise InstallError(f"refusing to adopt an unmanaged command path: {mapping['link']}")
                command_links.append((link, target))
            else:
                command_links.append((link, target))

    staged_receipt = _write_receipt(destination, collection_digest(staging), commands, source)

    backup: Path | None = None
    receipt_backup: Path | None = None
    installed_links: list[Path] = []
    replaced_links: list[tuple[Path, str]] = []
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
        for link, _ in command_links:
            if link.is_symlink():
                replaced_links.append((link, os.readlink(link)))
                link.unlink()
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
        if siyuan_config_update is not None:
            path, before, after = siyuan_config_update
            if codex_static.read(path) != before:
                raise codex_static.StaticError("SiYuan config changed concurrently")
            codex_static.write(path, after)
            if codex_static.read(path) != after:
                raise codex_static.StaticError("SiYuan config update verification failed")
    except (OSError, InstallError, codex_static.StaticError) as error:
        rollback_error = None
        if siyuan_config_update is not None:
            path, before, after = siyuan_config_update
            try:
                current = codex_static.read(path)
                if current == after:
                    codex_static.write(path, before)
                elif current != before:
                    raise InstallError("SiYuan config changed during rollback")
            except (OSError, InstallError, codex_static.StaticError) as failure:
                rollback_error = failure
        for link in installed_links:
            link.unlink(missing_ok=True)
        for link, target_text in reversed(replaced_links):
            if not link.exists() and not link.is_symlink():
                link.symlink_to(target_text)
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
        if rollback_error is not None:
            raise InstallError("collection replacement failed and rollback was incomplete") from error
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
    source: dict | None = None,
) -> bool:
    state = collection_state(expected_names, destination, bootstrap_name)
    if destination.name == "pennix-skills-extra" or source is not None:
        if destination.name != "pennix-skills-extra" or not valid_collection_source(source) or source["skills"] != sorted(expected_names) or commands or bootstrap_name is not None:
            raise InstallError("managed collection source identity is invalid")
        if state == "missing" and (receipt_path(destination).exists() or receipt_path(destination).is_symlink()):
            raise InstallError("refusing an orphaned managed collection receipt")
    if state == "missing":
        return False
    if state not in {"match", "bootstrap"}:
        raise InstallError("refusing to remove a non-exact Pennix Skills collection")
    commands = commands or {}
    allowed_integrity = {"match", "upgrade-available"} if source is not None else {"match"}
    if state == "match" and collection_receipt_state(destination, commands, source) not in allowed_integrity:
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
