#!/usr/bin/env python3
"""Read-only structural checks for explicitly selected Trellis document assets."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
# The negative lookahead prevents the quantifier from backtracking and treating
# the second '#' in a valid '## Heading' line as the heading's first character.
BAD_HEADING = re.compile(r"^#{1,6}(?!#)\S")
FENCE = re.compile(r"^[ \t]{0,3}([`~])\1{2,}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument("--paths", nargs="+", help="Explicit file or directory paths under --root")
    selected.add_argument(
        "--tracked-markdown",
        action="store_true",
        help="Discover current Git-tracked and pending Markdown files under --root",
    )
    parser.add_argument(
        "--links-only",
        action="store_true",
        help="Check only Markdown link targets and UTF-8 readability",
    )
    parser.add_argument("--max-files", type=int, default=200)
    return parser.parse_args()


def collect_files(root: Path, selected: list[str], max_files: int) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    root = root.resolve()

    for value in selected:
        target = (root / value).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f"path outside root: {value}")
            continue
        if not target.exists():
            errors.append(f"missing path: {value}")
            continue
        if target.is_file():
            files.append(target)
            continue
        for child in sorted(target.rglob("*")):
            if (
                child.is_file()
                and ".git" not in child.parts
                and "__pycache__" not in child.parts
                and child.suffix != ".pyc"
            ):
                files.append(child.resolve())

    unique = list(dict.fromkeys(files))
    if len(unique) > max_files:
        errors.append(f"file count {len(unique)} exceeds max-files {max_files}")
        unique = unique[:max_files]
    return unique, errors


def collect_tracked_markdown_files(root: Path, max_files: int) -> tuple[list[Path], list[str]]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return [], [f"Git Markdown discovery failed with exit {result.returncode}"]

    files: list[Path] = []
    errors: list[str] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        value = raw_path.decode("utf-8", errors="surrogateescape")
        candidate = Path(value)
        if candidate.is_absolute():
            errors.append(f"Git Markdown path is absolute: {value}")
            continue
        target = (root / candidate).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f"Git Markdown path outside root: {value}")
            continue
        if target.is_file():
            files.append(target)

    unique = list(dict.fromkeys(files))
    if len(unique) > max_files:
        errors.append(f"file count {len(unique)} exceeds max-files {max_files}")
        unique = unique[:max_files]
    return unique, errors


def is_escaped(value: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and value[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def fence_delimiter(line: str) -> tuple[str, int] | None:
    match = FENCE.match(line)
    if match is None:
        return None
    marker = match.group(0).lstrip(" \t")
    return marker[0], len(marker)


def closes_fence(line: str, character: str, minimum_length: int) -> bool:
    delimiter = fence_delimiter(line)
    if delimiter is None:
        return False
    observed_character, observed_length = delimiter
    match = FENCE.match(line)
    assert match is not None
    return (
        observed_character == character
        and observed_length >= minimum_length
        and not line[match.end():].strip(" \t")
    )


def mask_inline_code(line: str, active_delimiter_length: int | None) -> tuple[str, int | None]:
    masked: list[str] = []
    index = 0
    delimiter_length = active_delimiter_length
    while index < len(line):
        character = line[index]
        if character != "`":
            masked.append(" " if delimiter_length is not None and character not in "\r\n" else character)
            index += 1
            continue

        run_end = index + 1
        while run_end < len(line) and line[run_end] == "`":
            run_end += 1
        run_length = run_end - index
        if delimiter_length is None:
            if is_escaped(line, index):
                masked.append(line[index:run_end])
            else:
                delimiter_length = run_length
                masked.append(" " * run_length)
        else:
            masked.append(" " * run_length)
            if run_length == delimiter_length:
                delimiter_length = None
        index = run_end
    return "".join(masked), delimiter_length


def mask_markdown_code(text: str) -> str:
    masked_lines: list[str] = []
    fence: tuple[str, int] | None = None
    inline_delimiter_length: int | None = None
    for source_line in text.splitlines(keepends=True):
        line = source_line.rstrip("\r\n")
        line_ending = source_line[len(line):]
        if fence is not None:
            if closes_fence(line, *fence):
                fence = None
            masked_lines.append(line_ending)
            continue
        if inline_delimiter_length is None:
            opening_fence = fence_delimiter(line)
            if opening_fence is not None:
                fence = opening_fence
                masked_lines.append(line_ending)
                continue
        masked_line, inline_delimiter_length = mask_inline_code(line, inline_delimiter_length)
        masked_lines.append(masked_line + line_ending)
    return "".join(masked_lines)


def check_markdown_links(root: Path, path: Path, masked_text: str) -> list[str]:
    errors: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(masked_text):
        target = raw_target.strip().strip("<>").split("#", 1)[0]
        if not target or re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", target, re.I):
            continue
        link_path = (path.parent / unquote(target)).resolve()
        try:
            link_path.relative_to(root)
        except ValueError:
            errors.append(f"{path.relative_to(root)}: link outside root: {target}")
            continue
        if not link_path.exists():
            errors.append(f"{path.relative_to(root)}: missing link target: {target}")
    return errors


def check_text(root: Path, path: Path, links_only: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{path.relative_to(root)}: not valid UTF-8"]
    except OSError as exc:
        return [f"{path.relative_to(root)}: unreadable ({exc.__class__.__name__})"]
    if path.suffix.lower() == ".md":
        masked_text = mask_markdown_code(text)
        if links_only:
            return check_markdown_links(root, path, masked_text)
    else:
        masked_text = text
    if not text.strip():
        errors.append(f"{path.relative_to(root)}: empty text file")
    for line_number, (line, masked_line) in enumerate(
        zip(text.splitlines(), masked_text.splitlines()), start=1
    ):
        if line.rstrip(" \t") != line:
            errors.append(f"{path.relative_to(root)}:{line_number}: trailing whitespace")
        if path.suffix.lower() == ".md" and BAD_HEADING.match(masked_line):
            errors.append(f"{path.relative_to(root)}:{line_number}: heading needs a space")
    if path.suffix.lower() == ".md":
        errors.extend(check_markdown_links(root, path, masked_text))
    return errors


def check_json(root: Path, path: Path) -> list[str]:
    if path.suffix.lower() != ".json":
        return []
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{path.relative_to(root)}: invalid JSON ({exc.__class__.__name__})"]
    return []


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print("root is not a directory", file=sys.stderr)
        return 2

    if args.tracked_markdown:
        paths, errors = collect_tracked_markdown_files(root, args.max_files)
    else:
        assert args.paths is not None
        paths, errors = collect_files(root, args.paths, args.max_files)
    for path in paths:
        errors.extend(check_text(root, path, links_only=args.links_only))
        if not args.links_only:
            errors.extend(check_json(root, path))

    if errors:
        print(f"FAIL: {len(errors)} structural issue(s) in {len(paths)} file(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: checked {len(paths)} selected file(s); structural checks only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
