#!/usr/bin/env python3
"""Render a bounded new-session prompt from a validated project handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


HANDOFF_PATH = ".trellis/session-handoff.json"
SCRIPT_PATH = Path(__file__).with_name("handoff.py")
MAX_PAYLOAD_BYTES = 64 * 1024
MAX_PROJECT_ROOT_BYTES = 2048
MAX_TASK_PATH_BYTES = 1024
MAX_NEXT_ACTION_BYTES = 1024


class PromptError(RuntimeError):
    """Raised when a handoff cannot safely become a new-session prompt."""


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description="Render a ready Trellis session-handoff entry prompt")
    argument_parser.add_argument("--project-root", required=True, help="canonical Trellis project root")
    return argument_parser


def _safe_text(value: Any, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum:
        raise PromptError(f"{label} is invalid")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise PromptError(f"{label} contains control characters")
    return value


def _helper_path() -> Path:
    helper = SCRIPT_PATH
    if helper.is_symlink() or not helper.is_file():
        raise PromptError("session-handoff helper is unavailable")
    return helper


def _read_payload(project_root: Path) -> Mapping[str, Any]:
    helper = _helper_path()
    try:
        result = subprocess.run(
            [sys.executable, str(helper), "--project-root", str(project_root), "validate"],
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PromptError("handoff validate could not be completed") from exc
    if result.returncode != 0:
        try:
            status = json.loads(result.stdout).get("status")
        except (TypeError, json.JSONDecodeError):
            status = None
        if status:
            raise PromptError(f"handoff is not ready: {status}")
        raise PromptError("handoff validate could not be completed")
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PromptError("handoff validate returned invalid JSON") from exc
    if not isinstance(receipt, Mapping) or receipt.get("status") != "ready":
        raise PromptError("handoff is not ready")

    handoff = project_root / HANDOFF_PATH
    if handoff.is_symlink() or not handoff.is_file():
        raise PromptError("handoff file is unavailable")
    try:
        raw = handoff.read_bytes()
    except OSError as exc:
        raise PromptError("handoff file could not be read") from exc
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise PromptError("handoff file is too large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromptError("handoff file is invalid") from exc
    if not isinstance(payload, Mapping) or payload.get("schema_version") != 3 or payload.get("kind") != "trellis-session-handoff":
        raise PromptError("handoff file has an unsupported schema")
    return payload


def _task_text(payload: Mapping[str, Any]) -> str:
    context = payload.get("work_context")
    task = context.get("task") if isinstance(context, Mapping) else None
    if task is None:
        return "无活动 task（正常；据已核验项目事实选择或创建下一项 task）"
    if not isinstance(task, Mapping):
        raise PromptError("handoff task context is invalid")
    path = _safe_text(task.get("path"), "handoff task path", MAX_TASK_PATH_BYTES)
    if not path.startswith(".trellis/tasks/") or "/archive/" in path:
        raise PromptError("handoff task path is invalid")
    return json.dumps(path, ensure_ascii=False)


def render(project_root: Path, payload: Mapping[str, Any]) -> str:
    root_text = _safe_text(str(project_root), "project root", MAX_PROJECT_ROOT_BYTES)
    pending = payload.get("pending")
    if not isinstance(pending, Mapping):
        raise PromptError("handoff pending context is invalid")
    next_action = _safe_text(pending.get("next_action"), "handoff next action", MAX_NEXT_ACTION_BYTES)
    return (
        f"在 {json.dumps(root_text, ensure_ascii=False)} 新开 Codex 会话。先读取 `AGENTS.md` 和 `.trellis/workflow.md`，再使用 "
        f"`$session-handoff` 对 `{HANDOFF_PATH}` 重跑 `handoff validate`；只有 receipt 为 `ready` 才继续。\n"
        "receipt 为 `ready` 后，使用 `$trellis-start` 重新读取当前项目状态；若确认存在活动 task，再使用 "
        "`$trellis-continue` 选择当前 workflow step。\n"
        f"已验证导航（不覆盖新用户指令或 Trellis/Issue/Git 事实）：task={_task_text(payload)}；next_action={json.dumps(next_action, ensure_ascii=False)}。\n"
        "若 receipt 不是 `ready`，停止自动推进，按该状态重新核验项目事实。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        project_root = Path(args.project_root).expanduser().resolve(strict=True)
        payload = _read_payload(project_root)
        print(render(project_root, payload))
        return 0
    except (OSError, PromptError) as exc:
        print(f"session-handoff: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
