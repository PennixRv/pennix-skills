#!/usr/bin/env python3
"""Validate and merge reviewed user-level Codex Hook fragments."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import stat
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


INLINE_HOOK = re.compile(r"^\s*\[\[hooks\.[^\]]+\]\]")
INLINE_HOOK_HEADER = re.compile(
    r"^\s*\[\[hooks\.([A-Za-z][A-Za-z0-9_-]*)(?:\.hooks)?\]\]\s*(?:#.*)?$"
)
TOML_TABLE_HEADER = re.compile(r"^\s*\[\[?[^\]]+\]\]?\s*(?:#.*)?$")
CODEX_HOOK_EVENTS = {
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PreCompact",
    "PostCompact",
    "UserPromptSubmit",
    "SubagentStop",
    "Stop",
    "Interrupt",
    "SessionStart",
    "SubagentStart",
    "SessionEnd",
}
ALLOWED_FRAGMENT_KEYS = {"description", "hooks"}
ALLOWED_HANDLER_TYPES = {"command", "mcp_tool", "prompt", "agent"}


class RegistrationError(ValueError):
    """Raised when a Hook fragment or target is unsafe to process."""


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RegistrationError(f"{label} does not exist: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise RegistrationError(f"{label} is not valid JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise RegistrationError(f"{label} must contain a JSON object: {path}")
    return value


def validate_hook_config(value: dict[str, Any], label: str, fragment: bool) -> None:
    if fragment:
        unknown = set(value) - ALLOWED_FRAGMENT_KEYS
        if unknown:
            names = ", ".join(sorted(unknown))
            raise RegistrationError(f"{label} has unsupported top-level keys: {names}")

    hooks = value.get("hooks")
    if not isinstance(hooks, dict) or (fragment and not hooks):
        requirement = "a non-empty object" if fragment else "an object"
        raise RegistrationError(f"{label} must contain {requirement} at hooks")

    for event, groups in hooks.items():
        if not isinstance(event, str) or not event:
            raise RegistrationError(f"{label} contains an invalid event name")
        if not isinstance(groups, list) or not groups:
            raise RegistrationError(f"{label} event {event} must contain a non-empty array")
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                raise RegistrationError(f"{label} event {event}[{group_index}] must be an object")
            matcher = group.get("matcher")
            if matcher is not None and not isinstance(matcher, str):
                raise RegistrationError(f"{label} event {event}[{group_index}] has a non-string matcher")
            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                raise RegistrationError(f"{label} event {event}[{group_index}] must contain hooks")
            for handler_index, handler in enumerate(handlers):
                if not isinstance(handler, dict):
                    raise RegistrationError(
                        f"{label} event {event}[{group_index}].hooks[{handler_index}] must be an object"
                    )
                handler_type = handler.get("type")
                if handler_type not in ALLOWED_HANDLER_TYPES:
                    raise RegistrationError(
                        f"{label} event {event}[{group_index}].hooks[{handler_index}] "
                        f"has unsupported type: {handler_type!r}"
                    )
                if handler_type == "command" and not isinstance(handler.get("command"), str):
                    raise RegistrationError(
                        f"{label} event {event}[{group_index}].hooks[{handler_index}] "
                        "must contain a string command"
                    )
                for key in ("timeout", "additionalContextLimit"):
                    if key in handler and (
                        not isinstance(handler[key], int) or isinstance(handler[key], bool) or handler[key] <= 0
                    ):
                        raise RegistrationError(
                            f"{label} event {event}[{group_index}].hooks[{handler_index}] "
                            f"has invalid positive integer {key}"
                        )
                if "async" in handler and not isinstance(handler["async"], bool):
                    raise RegistrationError(
                        f"{label} event {event}[{group_index}].hooks[{handler_index}] has invalid async"
                    )


def assert_no_inline_hooks(config_path: Path) -> None:
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    except OSError as error:
        raise RegistrationError(f"Unable to read Codex config: {config_path}: {error}") from error
    for line_number, line in enumerate(lines, start=1):
        match = INLINE_HOOK_HEADER.match(line)
        if match and match.group(1) == "state":
            continue
        if INLINE_HOOK.match(line):
            raise RegistrationError(
                f"inline Codex Hook found in {config_path}:{line_number}; "
                "resolve it before registering user hooks.json"
            )


def read_toml(config_path: Path) -> tuple[str, dict[str, Any]]:
    try:
        content = config_path.read_text(encoding="utf-8")
        parsed = tomllib.loads(content)
    except FileNotFoundError as error:
        raise RegistrationError(f"Codex config does not exist: {config_path}") from error
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise RegistrationError(f"Codex config is not valid TOML: {config_path}: {error}") from error
    return content, parsed


def extract_inline_hooks(content: str, parsed: dict[str, Any]) -> dict[str, Any]:
    hook_table = parsed.get("hooks", {})
    if not isinstance(hook_table, dict):
        raise RegistrationError("Codex config hooks must be a TOML table")

    unsupported: list[str] = []
    for line in content.splitlines():
        match = INLINE_HOOK_HEADER.match(line)
        if match and match.group(1) not in CODEX_HOOK_EVENTS:
            unsupported.append(match.group(1))
    if unsupported:
        names = ", ".join(sorted(set(unsupported)))
        raise RegistrationError(f"unsupported inline Codex Hook event(s): {names}")

    fragment_hooks: dict[str, Any] = {}
    for event in CODEX_HOOK_EVENTS:
        value = hook_table.get(event)
        if value is not None:
            if not isinstance(value, list):
                raise RegistrationError(f"inline Codex Hook event {event} is not an array")
            fragment_hooks[event] = value
    fragment = {"hooks": fragment_hooks}
    if fragment_hooks:
        validate_hook_config(fragment, "inline Hook fragment", fragment=True)
    return fragment


def remove_inline_hooks(content: str) -> str:
    lines = content.splitlines(keepends=True)
    remove_ranges: list[tuple[int, int]] = []
    for index, line in enumerate(lines):
        match = INLINE_HOOK_HEADER.match(line)
        if not match:
            continue
        if match.group(1) not in CODEX_HOOK_EVENTS:
            raise RegistrationError(f"unsupported inline Codex Hook event: {match.group(1)}")
        end = index + 1
        while end < len(lines) and not TOML_TABLE_HEADER.match(lines[end]):
            end += 1
        remove_ranges.append((index, end))

    if not remove_ranges:
        return content
    removed = {index for start, end in remove_ranges for index in range(start, end)}
    return "".join(line for index, line in enumerate(lines) if index not in removed)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def merge_hooks(target: dict[str, Any], fragment: dict[str, Any]) -> tuple[dict[str, Any], int]:
    merged = copy.deepcopy(target)
    target_hooks = merged.setdefault("hooks", {})
    if not isinstance(target_hooks, dict):
        raise RegistrationError("target hooks must be a JSON object")
    additions = 0
    for event, groups in fragment["hooks"].items():
        existing = target_hooks.setdefault(event, [])
        if not isinstance(existing, list):
            raise RegistrationError(f"target event {event} must contain a JSON array")
        known = {canonical(group) for group in existing}
        for group in groups:
            marker = canonical(group)
            if marker not in known:
                existing.append(group)
                known.add(marker)
                additions += 1
    return merged, additions


def write_bytes_atomic(path: Path, content: bytes, mode: int) -> None:
    if path.is_symlink():
        raise RegistrationError(f"destination must not be a symbolic link: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    except OSError as error:
        raise RegistrationError(f"Unable to prepare destination {path}: {error}") from error
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, mode)
    except OSError as error:
        raise RegistrationError(f"Unable to write destination {path}: {error}") from error
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    content = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    write_bytes_atomic(path, content, 0o600)


def resolve_paths(args: argparse.Namespace) -> tuple[Path | None, Path, Path]:
    codex_dir = default_codex_home()
    destination = Path(args.destination).expanduser() if args.destination else codex_dir / "hooks.json"
    config_path = Path(args.config).expanduser() if args.config else codex_dir / "config.toml"
    raw_fragment = getattr(args, "fragment", None)
    fragment_path = Path(raw_fragment).expanduser() if raw_fragment else None
    return fragment_path, destination, config_path


def validate_command(args: argparse.Namespace) -> int:
    fragment_path, _, config_path = resolve_paths(args)
    if fragment_path is None:
        raise RegistrationError("Hook fragment is required")
    fragment = load_json(fragment_path, "Hook fragment")
    validate_hook_config(fragment, "Hook fragment", fragment=True)
    if args.check_config:
        assert_no_inline_hooks(config_path)
    print(f"Validated Hook fragment: {fragment_path}")
    return 0


def merge_command(args: argparse.Namespace) -> int:
    fragment_path, destination, config_path = resolve_paths(args)
    if fragment_path is None:
        raise RegistrationError("Hook fragment is required")
    fragment = load_json(fragment_path, "Hook fragment")
    validate_hook_config(fragment, "Hook fragment", fragment=True)
    assert_no_inline_hooks(config_path)

    target = load_json(destination, "existing hooks.json") if destination.exists() else {"hooks": {}}
    validate_hook_config(target, "existing hooks.json", fragment=False)
    merged, additions = merge_hooks(target, fragment)
    if args.dry_run:
        print(f"Would add {additions} matcher group(s) to {destination}")
        return 0
    write_json_atomic(destination, merged)
    print(f"Added {additions} matcher group(s) to {destination}")
    return 0


def write_text_atomic(path: Path, content: str) -> None:
    write_bytes_atomic(path, content.encode("utf-8"), 0o600)


def snapshot_file(path: Path) -> tuple[bytes, int] | None:
    if path.is_symlink():
        raise RegistrationError(f"destination must not be a symbolic link: {path}")
    try:
        metadata = path.stat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise RegistrationError(f"Unable to inspect destination {path}: {error}") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise RegistrationError(f"destination must be a regular file: {path}")
    try:
        return path.read_bytes(), stat.S_IMODE(metadata.st_mode)
    except OSError as error:
        raise RegistrationError(f"Unable to read destination {path}: {error}") from error


def restore_snapshot(path: Path, snapshot: tuple[bytes, int] | None) -> None:
    if snapshot is not None:
        content, mode = snapshot
        write_bytes_atomic(path, content, mode)
        return
    if path.is_symlink():
        raise RegistrationError(f"destination must not be a symbolic link: {path}")
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        raise RegistrationError(f"Unable to remove new destination {path}: {error}") from error


def migrate_command(args: argparse.Namespace) -> int:
    _, destination, config_path = resolve_paths(args)
    content, parsed = read_toml(config_path)
    fragment = extract_inline_hooks(content, parsed)
    if not fragment["hooks"]:
        print(f"No supported inline Codex Hook definitions found in {config_path}")
        return 0

    destination_snapshot = snapshot_file(destination)
    target = load_json(destination, "existing hooks.json") if destination_snapshot is not None else {"hooks": {}}
    validate_hook_config(target, "existing hooks.json", fragment=False)
    merged, additions = merge_hooks(target, fragment)
    cleaned = remove_inline_hooks(content)
    if INLINE_HOOK.search(cleaned):
        raise RegistrationError(f"inline Codex Hook definitions remain after migration: {config_path}")

    events = ", ".join(sorted(fragment["hooks"]))
    print(f"Found inline Hook event(s) in {config_path}: {events}")
    print(f"Would add {additions} matcher group(s) to {destination}")
    if not args.apply:
        print("Preview only; rerun with --apply to update hooks.json and remove these inline definitions")
        return 0

    write_json_atomic(destination, merged)
    try:
        write_text_atomic(config_path, cleaned)
    except RegistrationError as error:
        try:
            restore_snapshot(destination, destination_snapshot)
        except RegistrationError as rollback_error:
            raise RegistrationError(
                "config.toml was not migrated and hooks.json rollback failed: "
                f"{rollback_error}; original error: {error}"
            ) from rollback_error
        raise RegistrationError(f"config.toml was not migrated; hooks.json was restored: {error}") from error
    print(f"Migrated {additions} matcher group(s) and removed inline definitions from {config_path}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="action", required=True)

    validate = subcommands.add_parser("validate", help="validate a reviewed Hook fragment")
    validate.add_argument("--fragment", required=True)
    validate.add_argument("--config", help="Codex config.toml to inspect")
    validate.add_argument("--check-config", action="store_true")
    validate.set_defaults(handler=validate_command)

    merge = subcommands.add_parser("merge", help="merge a reviewed fragment into user hooks.json")
    merge.add_argument("--fragment", required=True)
    merge.add_argument("--dest", dest="destination", help="destination hooks.json")
    merge.add_argument("--config", help="Codex config.toml to inspect")
    merge.add_argument("--dry-run", action="store_true")
    merge.set_defaults(handler=merge_command)

    migrate = subcommands.add_parser(
        "migrate", help="preview or migrate inline user hooks from config.toml"
    )
    migrate.add_argument("--config", help="Codex config.toml containing inline Hooks")
    migrate.add_argument("--dest", dest="destination", help="destination hooks.json")
    migrate.add_argument("--apply", action="store_true", help="write hooks.json and remove inline Hook tables")
    migrate.set_defaults(handler=migrate_command)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        return args.handler(args)
    except RegistrationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
