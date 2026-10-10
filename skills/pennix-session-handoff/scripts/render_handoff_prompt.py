#!/usr/bin/env python3
"""将一个 ready 的 Pennix 会话交接包渲染为配对入口提示词。"""

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
    argument_parser.add_argument("--project-root", required=True, help="规范 Trellis 项目根目录")
    argument_parser.add_argument("--handoff", required=True, help="项目相对的带时间戳交接 JSON 路径")
    return argument_parser


def _helper_path() -> Path:
    if SCRIPT_PATH.is_symlink() or not SCRIPT_PATH.is_file():
        raise PromptError("pennix-session-handoff 辅助程序不可用")
    return SCRIPT_PATH


def _run_validate(root: Path, handoff: str) -> Mapping[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, str(_helper_path()), "--project-root", str(root), "validate", "--handoff", handoff],
            text=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PromptError("无法完成 handoff validate") from exc
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PromptError("handoff validate 返回了无效 JSON") from exc
    if result.returncode != 0 or not isinstance(receipt, Mapping) or receipt.get("status") != "ready":
        status = receipt.get("status") if isinstance(receipt, Mapping) else None
        raise PromptError("handoff 未就绪%s" % (": " + str(status) if status else ""))
    return receipt


def _run_lifecycle_status(root: Path, handoff: str) -> Mapping[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, str(_helper_path()), "--project-root", str(root), "status", "--handoff", handoff],
            text=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PromptError("无法完成 handoff lifecycle status") from exc
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PromptError("handoff lifecycle status 返回了无效 JSON") from exc
    if result.returncode != 0 or not isinstance(receipt, Mapping) or receipt.get("status") not in {"absent", "ready", "historical"}:
        status = receipt.get("status") if isinstance(receipt, Mapping) else None
        raise PromptError("handoff lifecycle 未就绪%s" % (": " + str(status) if status else ""))
    return receipt


def _payload(root: Path, relative: str) -> Mapping[str, Any]:
    candidate = root / relative
    if Path(relative).is_absolute() or candidate.is_symlink() or not candidate.is_file():
        raise PromptError("handoff 文件不可用")
    raw = candidate.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromptError("handoff 文件无效") from exc
    if not isinstance(payload, Mapping) or payload.get("schema_version") not in {8, 9} or payload.get("kind") != "pennix-session-handoff":
        raise PromptError("handoff 文件的 schema 不受支持")
    return payload


def _markdown_list(values: Any) -> str:
    if not isinstance(values, list) or not values:
        return "- 无\n"
    return "".join("- %s\n" % str(value) for value in values)


def _render_document(root: Path, relative: str, payload: Mapping[str, Any]) -> str:
    source = payload["source"]
    pending = payload["pending"]
    work_context = payload["work_context"]
    task = work_context.get("task") if isinstance(work_context, Mapping) else None
    task_text = "未记录当前任务。"
    if isinstance(task, Mapping):
        task_text = "`%s` (%s, %s)" % (task.get("path"), task.get("id"), task.get("status"))
    git = source["git"]
    rollout = source["rollout"]
    conversation = payload["conversation"]
    memory = payload.get("memory_projection", {})
    if not isinstance(memory, Mapping):
        memory = {}
    lines = [
        "# Pennix 会话交接", "",
        "这是导航包，不是转录、任务数据库或继续执行的授权。",
        "下一位协调代理必须重新核验本包，再读取当前项目事实。", "",
        "## 身份", "", "- 交接 ID：`%s`" % payload["handoff_id"], "- 创建时间：`%s`" % payload["created_at"],
        "- 项目：`%s`" % root, "- 包 JSON：`%s`" % relative, "- 会话标签：%s" % source["session_label"], "",
        "## 新会话必经路径", "",
        "1. 读取 `AGENTS.md` 和 `.trellis/workflow.md`。",
        "2. 对精确的包 JSON 运行 `$pennix-session-handoff` 核验。",
        "3. 只有 receipt 为 `ready` 时，才完整读取配对包 JSON 和本交接提示词，然后处理 `Pending`。",
        "4. 运行 `$trellis-start`，再将捕获的任务、Git 状态、证据和 pending action 与当前事实比较。",
        "5. 初次接纳期间不要调用 `task.py start` 或 claim 归属，也不要从此快照关闭任务。完整的读取、启动和协调序列结束前不要记录接纳；中断的序列不算消费。",
        "6. 后续用户指令授权继续此任务时，先使用交接归属 `claim` 操作；它只绑定当前直接目标会话，然后使用 `$trellis-continue` 处理实际分类和阶段。只读 `analysis_only` 研究保持 planning，不调用 `task.py start`；变更工作只有在当前原生 seal 和批准存在时才开始；已经运行的工作恢复其检查点。",
        "7. 工作被消费后，分别记录归属 `consume` 和归属 `archive`；正常任务生命周期使用 `$trellis-finish-work`。",
        "8. 协调后停止。没有后续用户指令时，不执行 pending next action，也不开始实施。",
        "9. 当前用户指令、Trellis、Issue 状态、Git 和当前文件是更高优先级事实。", "",
        "## 已核验项目快照", "", "- 任务：%s" % task_text,
        "- Git 分支：`%s`" % git.get("branch"), "- Git HEAD：`%s`" % git.get("head"),
        "- 捕获时工作树：`%s`" % git.get("worktree_state"),
        "- 最近提交：%s" % ", ".join("`%s`" % value for value in git.get("recent_commits", [])), "",
        "### 事实", "", _markdown_list(payload["verified"].get("facts")), "### 核验", "",
    ]
    validation = payload["verified"].get("validation", [])
    lines.extend("- `%s`: %s" % (item.get("command"), item.get("result")) for item in validation)
    if not validation:
        lines.append("- 无")
    lines.extend(["", "### 证据快照", ""])
    lines.extend("- `%s`" % item["path"] for item in source["evidence"])
    lines.extend([
        "", "## Rollout 覆盖范围与候选", "", "- 来源：`%s`" % rollout["path"],
        "- 捕获边界：字节 %d；记录数：%d" % (rollout["capture_end"], rollout["record_count"]),
        "- 解析器：`%s`" % rollout["parser_version"],
        "- 这些只是在本地对话中形成的候选，不能覆盖上面的已核验快照。", "",
        "## 语义交接摘要", "",
        memory.get("semantic_capsule") or "未提供额外语义摘要；以任务和当前事实为准。", "",
        "### 本地引用", "",
        _markdown_list(memory.get("local", [])),
        _markdown_list(memory.get("archive_refs", [])),
        "### 决策时间线", "",
    ])
    timeline = conversation.get("timeline", [])
    candidates = conversation.get("candidates", [])
    lines.extend([
        "- 完整时间线条目保留在包 JSON 的 `conversation.timeline` 中；数量：%d。" % len(timeline) if isinstance(timeline, list) else "- 完整时间线条目保留在包 JSON 的 `conversation.timeline` 中。",
        "- 重建决策和已被替代的方向时完整读取该字段。",
        "", "### 对话候选", "",
        "- 完整候选条目保留在包 JSON 的 `conversation.candidates` 中；数量：%d。" % len(candidates) if isinstance(candidates, list) else "- 完整候选条目保留在包 JSON 的 `conversation.candidates` 中。",
        "- 完整读取该字段；提示词有意不重复候选正文。",
        "", "### 覆盖范围说明", "",
        "- 完整覆盖范围和来源信息保留在包 JSON 的 `conversation.coverage` 中；完整读取。",
        "- 包 JSON 是规范资产；本提示词只是紧凑导航视图。",
        "", "## Pending", "", "- 下一步：%s" % pending["next_action"],
        "", "### 阻塞项", "", _markdown_list(pending["blockers"]), "### 风险", "", _markdown_list(pending["risks"]),
    ])
    return "\n".join(lines).rstrip() + "\n"


def _atomic_prompt(destination: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise PromptError("交接 prompt 路径不安全")
        if destination.read_bytes() != encoded:
            raise PromptError("配对 prompt 已存在且内容不同")
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
        raise PromptError("无法写入配对交接 prompt") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        root = Path(args.project_root).expanduser().resolve(strict=True)
        _run_validate(root, args.handoff)
        _run_lifecycle_status(root, args.handoff)
        payload = _payload(root, args.handoff)
        prompt_relative = str(Path(args.handoff).with_name(PROMPT_NAME))
        if payload["schema_version"] == 8:
            prompt = root / prompt_relative
            if prompt.is_symlink() or not prompt.is_file():
                raise PromptError("历史配对 prompt 不可用；只读审计不能创建它")
            prompt.read_text(encoding="utf-8")
            print("历史交接包仅供只读审计，不能准入或继续；原始 JSON 和配对 prompt 保持不变。")
            print(args.handoff + "\n" + prompt_relative)
            return 0
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
        print("pennix-session-handoff：%s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
