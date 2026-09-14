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


def _run_lifecycle_status(root: Path, handoff: str) -> Mapping[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, str(_helper_path()), "--project-root", str(root), "status", "--handoff", handoff],
            text=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PromptError("handoff lifecycle status could not be completed") from exc
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PromptError("handoff lifecycle status returned invalid JSON") from exc
    if not isinstance(receipt, Mapping) or receipt.get("status") not in {"absent", "ready"}:
        status = receipt.get("status") if isinstance(receipt, Mapping) else None
        raise PromptError("handoff lifecycle is not ready%s" % (": " + str(status) if status else ""))
    return receipt


def _payload(root: Path, relative: str) -> Mapping[str, Any]:
    candidate = root / relative
    if Path(relative).is_absolute() or candidate.is_symlink() or not candidate.is_file():
        raise PromptError("handoff file is unavailable")
    raw = candidate.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromptError("handoff file is invalid") from exc
    if not isinstance(payload, Mapping) or payload.get("schema_version") not in {4, 5, 6} or payload.get("kind") != "pennix-session-handoff":
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
    memory = payload.get("memory_projection", {})
    if not isinstance(memory, Mapping):
        memory = {}
    lines = [
        "# Pennix Session Handoff", "",
        "This is a navigation package, not a transcript, task database, or authorization to continue.",
        "The next coordinator must revalidate this package and then re-read current project facts.", "",
        "## Identity", "", "- Handoff ID: `%s`" % payload["handoff_id"], "- Created: `%s`" % payload["created_at"],
        "- Project: `%s`" % root, "- Package JSON: `%s`" % relative, "- Session label: %s" % source["session_label"], "",
        "## Required New-Session Route", "",
        "1. Read `AGENTS.md` and `.trellis/workflow.md`.",
        "2. Run `$pennix-session-handoff` validation for the exact package JSON.",
        "3. Only when the receipt is `ready`, read the paired package JSON and this entire handoff prompt before acting on `Pending`.",
        "4. Run `$trellis-start`, then compare the captured task, Git state, evidence, and pending action with current facts.",
        "5. Do not call `task.py start` or claim ownership during initial intake; do not close it from this snapshot, and record an admission only after reconciliation and stop.",
        "6. If a subsequent user instruction authorizes continuation of this task, use the handoff ownership `claim` operation first; it binds only this direct target session, then use `$trellis-continue` as appropriate.",
        "7. After work is consumed, record ownership `consume` and then ownership `archive` separately; use `$trellis-finish-work` for the normal task lifecycle.",
        "8. Stop after reconciliation. Do not execute the pending next action or begin implementation until a subsequent user instruction.",
        "9. Treat current user instructions, Trellis, Issue state, Git and current files as higher-priority facts.", "",
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
    lines.extend("- `%s`" % item["path"] for item in source["evidence"])
    lines.extend([
        "", "## Rollout Coverage And Candidates", "", "- Source: `%s`" % rollout["path"],
        "- Capture boundary: byte %d; records: %d" % (rollout["capture_end"], rollout["record_count"]),
        "- Parser: `%s`" % rollout["parser_version"],
        "- These are local conversation candidates only. They cannot override the verified snapshot above.", "",
        "## Semantic Handoff Capsule", "",
        memory.get("semantic_capsule") or "No additional semantic capsule was supplied; use the task and current facts as the source of truth.", "",
        "### Memory References", "",
        _markdown_list(memory.get("local", [])),
        _markdown_list(memory.get("archive_refs", [])),
        _markdown_list(memory.get("openviking", [])),
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
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        raise PromptError("could not write paired handoff prompt") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        root = Path(args.project_root).expanduser().resolve(strict=True)
        _run_validate(root, args.handoff)
        _run_lifecycle_status(root, args.handoff)
        payload = _payload(root, args.handoff)
        prompt_relative = str(Path(args.handoff).with_name(PROMPT_NAME))
        _atomic_prompt(root / prompt_relative, _render_document(root, args.handoff, payload))
        entry = (
            "当前会话位于 %s。先读取 `AGENTS.md` 和 `.trellis/workflow.md`，再使用 "
            "`$pennix-session-handoff` 对 `%s` 运行 `handoff validate --handoff %s`；只有 receipt 为 `ready` 才继续。"
            "随后完整阅读配对 JSON core `%s` 和 `%s`，按 `$trellis-start` 严格核对并收敛交接 task；不得执行 pending next action，停在可继续交接前会话任务的现场。"
            % (json.dumps(str(root), ensure_ascii=False), args.handoff, args.handoff, args.handoff, prompt_relative)
        )
        print("可直接复制到新会话的短提示词：\n\n```text\n%s\n```" % entry)
        return 0
    except (OSError, PromptError) as exc:
        print("pennix-session-handoff: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
