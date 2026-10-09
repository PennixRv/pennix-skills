---
name: pennix-fastctx-routing
description: Route FastCtx local-file, shell, and job operations by request semantics. Use whenever a task involves FastCtx and no more specific native protocol owns the action; do not use for FastCtx installation, host migration, or cross-component ownership decisions.
---

# Pennix FastCtx 路由

## 适用范围

对 FastCtx 的本地文件、命令或 job 操作使用本 Skill。安装、升级、主机迁移或回滚只由显式调用的
`$pennix-workflow-lifecycle` 处理；跨组件职责不清时改用 `$pennix-workflow-routing`。

每次路由都必须先完成 semantic owner preflight：先排除 workflow-native owner，再把没有
专用 owner 的普通本地操作交给 FastCtx。可执行文件位于本地、调用形式是 shell，或输出是
JSON，都不会改变其 owner；`grok-search`、lifecycle、Trellis、handoff、Hook、原生 MCP/TUI
以及其他专用组件不能因为这些表面特征被当成普通 CLI。

先判断是否存在原生 owner 协议。下列语义不属于 FastCtx，即使操作最终涉及本地文件、命令或等待：Trellis task
phase、task pointer、`task.py`、`trellis continue/start/check/finish`、正式 handoff 的
`handoff` CLI、Trellis Channel worker/`wait-next`、Codex 原生
`request_user_input`、Hook 事件和 Hook 诊断、原生 Plugin/MCP resource 与工具调用、owner
controlled TUI，以及 lifecycle 的受管 deployment/configure action。它们必须直接调用其原生接口；
原生接口不可用或调用被拒绝时，保留原错误并停止，绝不以 `run`、轮询、shell HTTP、文件替换或
FastCtx job 模拟、接管或绕过。

## 路由规则

工具可用性以当前会话宿主实际暴露的原生 MCP 工具为准。`functions.exec` 中的嵌套编排器
`ALL_TOOLS` 只列出可供该编排器调用的嵌套工具，不是宿主原生 MCP 清单；其缺少 FastCtx
名称不能证明 FastCtx 未安装或不可用。原生 FastCtx 工具已暴露时直接调用；仅当宿主未暴露
该原生工具时，普通本地操作才按下方规则降级。调用已暴露工具遇到 schema、权限、传输或
服务错误时保留原错误类别，不得改报为工具缺失。

1. 只有普通本地读取、搜索、非交互 CLI、构建、测试或明确 FastCtx job 语义通过 owner-first 排除后，才进入 FastCtx 路由。
2. 仅当工具 schema 支持批量且已知有多个文本文件时，使用 `inspect_local_file` 的 `files` 批量读取；单一目标或不同视图直接调用对应工具。
3. `run` 只承载一条非交互式 CLI；长时操作改用 `run_background`、`job_output`、`job_kill`。已有直接 FastCtx schema 的操作不再包一层 shell，也绝不把 `apply_patch` 传给 `run`。
4. 源码、配置、任务文档等文本的语义创建/修改使用宿主原生 `apply_patch`，不通过 `run`、`run_background` 或 shell/Python 写入脚本代写；专用 owner 生成的资产仍由该 owner 写入。只有确定性的批量机械替换才使用 FastCtx `replace`，并先 dry-run、设置替换上限。
5. `grok-search`、`tavily-hikari`、Windsurf semantic search 和 CodeGraph 保持各自的检索或 MCP/API owner；FastCtx 可在它们完成后分析一个已批准的本地结果文件，但不调用、代替或吸收其检索协议。
6. 项目 `AGENTS.md`、项目 spec 和已有专用协议优先；无法判断组件所有权时停止 FastCtx 路由，改用 `$pennix-workflow-routing` 收敛。

专用 owner 的 executable 或 CLI 禁止通过 FastCtx `run`、`run_background`、job、`replace`、
shell HTTP 或通用 wrapper 启动、转发、重试、轮询、等待或解释；owner native channel 不可用
时必须保留 blocked/capability-gap 结果。FastCtx 可以在 owner 已完成后读取已批准的普通结果
文件，但不得用该读取推进、确认或模拟 owner 状态。

FastCtx 不可用时，按项目规则降级到宿主原生工具；不把当前操作输出自动写入任务事实、记忆或 Git。

若误将 `task.py` 交给 FastCtx 后发生身份缺失，先纠正调用为当前宿主原生 shell
（Codex 的 `exec_command`），再用原生 `current --json` 区分身份与绑定：
`session_source` 非空表示身份存在，`unbound_task` / `unbound_ambiguous` 只表示没有
活动任务绑定。按用户明确意图原生 `select`，不把它当作实施批准。正确原生路径仍无身份
才报告能力缺口；不向 FastCtx 注入复制/猜造的身份，不手写 pointer 或 shell ticket。
