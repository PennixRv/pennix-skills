#!/usr/bin/env python3
"""Render one ready Pennix session-handoff package into its paired entry prompt."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SCRIPT_PATH = Path(__file__).with_name("handoff.py")
PROMPT_NAME = "session-handoff-prompt.md"
MAX_PAYLOAD_BYTES = 512 * 1024


class PromptError(RuntimeError):
    """Raised when a handoff cannot safely become a new-session prompt."""


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--project-root", required=True, help="canonical Trellis project root")
    argument_parser.add_argument("--handoff", required=True, help="project-relative timestamped handoff JSON path")
    return argument_parser


def _helper_path() -> Path:
    if SCRIPT_PATH.is_symlink() or not SCRIPT_PATH.is_file():
        raise PromptError("pennix-session-handoff helper is unavailable")
    return SCRIPT_PATH


def _run_validate(root: Path, handoff: str) -> Mapping[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, str(_helper_path()), "--project-root", str(root), "validate", "--handoff", handoff],
            text=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PromptError("handoff validate could not be completed") from exc
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PromptError("handoff validate returned invalid JSON") from exc
    if result.returncode != 0 or not isinstance(receipt, Mapping) or receipt.get("status") != "ready":
        status = receipt.get("status") if isinstance(receipt, Mapping) else None
        raise PromptError("handoff is not ready%s" % (": " + str(status) if status else ""))
    return receipt


def _payload(root: Path, relative: str) -> Mapping[str, Any]:
    candidate = root / relative
    if Path(relative).is_absolute() or candidate.is_symlink() or not candidate.is_file():
        raise PromptError("handoff file is unavailable")
    raw = candidate.read_bytes()
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise PromptError("handoff file is too large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromptError("handoff file is invalid") from exc
    if not isinstance(payload, Mapping) or payload.get("schema_version") != 4 or payload.get("kind") != "pennix-session-handoff":
        raise PromptError("handoff file has an unsupported schema")
    return payload


def _markdown_list(values: Any) -> str:
    if not isinstance(values, list) or not values:
        return "- None\n"
    return "".join("- %s\n" % str(value) for value in values)


def _render_document(root: Path, relative: str, payload: Mapping[str, Any]) -> str:
    source = payload["source"]
    pending = payload["pending"]
    work_context = payload["work_context"]
    task = work_context.get("task") if isinstance(work_context, Mapping) else None
    task_text = "No active task recorded."
    if isinstance(task, Mapping):
        task_text = "`%s` (%s, %s)" % (task.get("path"), task.get("id"), task.get("status"))
    git = source["git"]
    rollout = source["rollout"]
    conversation = payload["conversation"]
    lines = [
        "# Pennix Session Handoff", "",
        "This is a bounded navigation package, not a transcript, task database, or authorization to continue.",
        "The next coordinator must revalidate this package and then re-read current project facts.", "",
        "## Identity", "", "- Handoff ID: `%s`" % payload["handoff_id"], "- Created: `%s`" % payload["created_at"],
        "- Project: `%s`" % root, "- Package JSON: `%s`" % relative, "- Session label: %s" % source["session_label"], "",
        "## Required New-Session Route", "",
        "1. Read `AGENTS.md` and `.trellis/workflow.md`.",
        "2. Run `$pennix-session-handoff` validation for the exact package JSON.",
        "3. Only when the receipt is `ready`, run `$trellis-start` and reconcile the captured task with the current task.",
        "4. If current acceptance evidence proves that task complete, use `$trellis-finish-work` to close and archive it; otherwise do not close it from this snapshot.",
        "5. Use `$trellis-continue` only when the reconciled task still needs continuation.",
        "6. Treat current user instructions, Trellis, Issue state, Git and current files as higher-priority facts.", "",
        "## Verified Project Snapshot", "", "- Task: %s" % task_text,
        "- Git branch: `%s`" % git.get("branch"), "- Git HEAD: `%s`" % git.get("head"),
        "- Worktree at capture: `%s`" % git.get("worktree_state"),
        "- Recent commits: %s" % ", ".join("`%s`" % value for value in git.get("recent_commits", [])), "",
        "### Facts", "", _markdown_list(payload["verified"].get("facts")), "### Validation", "",
    ]
    validation = payload["verified"].get("validation", [])
    lines.extend("- `%s`: %s" % (item.get("command"), item.get("result")) for item in validation)
    if not validation:
        lines.append("- None")
    lines.extend(["", "### Evidence Snapshot", ""])
    lines.extend("- `%s` (%d bytes, `%s`)" % (item["path"], item["bytes"], item["sha256"]) for item in source["evidence"])
    lines.extend([
        "", "## Rollout Coverage And Candidates", "", "- Source: `%s`" % rollout["path"],
        "- Capture boundary: byte %d; records: %d; prefix: `%s`" % (rollout["capture_end"], rollout["record_count"], rollout["prefix_sha256"]),
        "- Parser: `%s`" % rollout["parser_version"],
        "- These are local conversation candidates only. They cannot override the verified snapshot above.", "",
        "### Decision Timeline", "",
    ])
    timeline = conversation.get("timeline", [])
    if timeline:
        lines.extend(
            "- `%s` at event %s: %s%s" % (
                item.get("topic_key"), item.get("event_index"), item.get("state"),
                " (supersedes event %s)" % item["supersedes_event_index"] if "supersedes_event_index" in item else "",
            ) for item in timeline
        )
    else:
        lines.append("- No stable explicit-topic timeline candidates were extracted.")
    lines.extend(["", "### Conversation Candidates", ""])
    candidates = conversation.get("candidates", [])
    if candidates:
        for item in candidates:
            text = item.get("text")
            lines.append("- [%s #%s] %s" % (item.get("kind"), item.get("event_index"), text or "metadata only"))
    else:
        lines.append("- No eligible public user/assistant/tool candidates were extracted.")
    lines.extend([
        "", "### Coverage Notes", "", "```json",
        json.dumps(conversation.get("coverage", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```", "", "## Pending", "", "- Next action: %s" % pending["next_action"],
        "", "### Blockers", "", _markdown_list(pending["blockers"]), "### Risks", "", _markdown_list(pending["risks"]),
    ])
    return "\n".join(lines).rstrip() + "\n"


def _atomic_prompt(destination: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise PromptError("handoff prompt path is unsafe")
        if destination.read_bytes() != encoded:
            raise PromptError("paired prompt already exists with different content")
        return
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    except OSError as exc:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        raise PromptError("could not write paired handoff prompt") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        root = Path(args.project_root).expanduser().resolve(strict=True)
        _run_validate(root, args.handoff)
        payload = _payload(root, args.handoff)
        prompt_relative = str(Path(args.handoff).with_name(PROMPT_NAME))
        _atomic_prompt(root / prompt_relative, _render_document(root, args.handoff, payload))
        print(
            "在 %s 新开 Codex 会话。先读取 `AGENTS.md` 和 `.trellis/workflow.md`，再使用 "
            "`$pennix-session-handoff` 对 `%s` 运行 `handoff validate --handoff %s`；只有 receipt 为 `ready` 才继续。"
            "完整交接提示词位于 `%s`；随后按 `$trellis-start` 核对并闭合已完成的交接 task，仅对仍需继续的 task 按 `$trellis-continue`。"
            % (json.dumps(str(root), ensure_ascii=False), args.handoff, args.handoff, prompt_relative)
        )
        return 0
    except (OSError, PromptError) as exc:
        print("pennix-session-handoff: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
