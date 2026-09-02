#!/usr/bin/env python3
"""Prepare a user-approved CodeGraph project configuration without indexing."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def git_value(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def resolve_project(start: Path) -> tuple[Path, bool]:
    try:
        root = Path(git_value(start, "rev-parse", "--show-toplevel")).resolve()
        git_dir_value = git_value(root, "rev-parse", "--git-dir")
        common_dir_value = git_value(root, "rev-parse", "--git-common-dir")
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"无法解析 Git 项目根：{error}") from error

    git_dir = Path(git_dir_value)
    common_dir = Path(common_dir_value)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    if not common_dir.is_absolute():
        common_dir = root / common_dir
    return root, git_dir.resolve() != common_dir.resolve()


def load_config(path: Path) -> tuple[dict[str, object], str]:
    if not path.exists():
        return {}, ""
    try:
        original = path.read_text(encoding="utf-8")
        value = json.loads(original)
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"无法读取 {path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"{path} 必须是 JSON 对象")
    return value, original


def validate_pattern(pattern: str) -> str:
    normalized = pattern.strip()
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        raise SystemExit(f"不接受不安全的排除模式：{pattern!r}")
    return normalized


def prepare_config(
    value: dict[str, object], extra_excludes: list[str]
) -> dict[str, object]:
    prepared = dict(value)
    excludes = prepared.get("exclude", [])
    if not isinstance(excludes, list) or not all(
        isinstance(item, str) for item in excludes
    ):
        raise SystemExit("codegraph.json 的 exclude 必须是字符串数组")

    additions = [".trellis/"] + [validate_pattern(item) for item in extra_excludes]
    prepared["exclude"] = list(excludes)
    for pattern in additions:
        if pattern not in prepared["exclude"]:
            prepared["exclude"].append(pattern)
    return prepared


def render(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write_atomic(path: Path, content: str) -> None:
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="展示或写入 CodeGraph 项目的最小安全排除规则"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="项目目录，默认使用当前目录并解析其 Git 项目根",
    )
    parser.add_argument(
        "--extra-exclude",
        action="append",
        default=[],
        help="用户已批准的额外 gitignore 风格排除模式，可重复",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="写入 codegraph.json；默认只显示差异",
    )
    arguments = parser.parse_args()
    start = (arguments.project_root or Path.cwd()).resolve()
    project_root, linked = resolve_project(start)
    print(f"project_root: {project_root}")
    print(f"worktree: {'linked' if linked else 'main'}")
    if linked:
        raise SystemExit("拒绝 linked Git worktree；请从普通主工作树运行。")

    config_path = project_root / "codegraph.json"
    current, original = load_config(config_path)
    prepared = prepare_config(current, arguments.extra_exclude)
    updated = render(prepared)
    if original == updated:
        print("codegraph.json: 无需修改")
        return 0

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=str(config_path) if original else "/dev/null",
        tofile=str(config_path),
    )
    print("".join(diff), end="")
    if arguments.apply:
        write_atomic(config_path, updated)
        print(f"已写入: {config_path}")
    else:
        print("预览模式：未写入文件。用户确认后重新添加 --apply。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
