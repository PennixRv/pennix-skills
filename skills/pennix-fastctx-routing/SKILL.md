---
name: pennix-fastctx-routing
description: Route FastCtx local-file, shell, and job operations by request semantics. Use whenever a task involves FastCtx and no more specific native protocol owns the action; do not use for FastCtx installation, host migration, or cross-component ownership decisions.
---

# Pennix FastCtx 路由

## 适用范围

对 FastCtx 的本地文件、命令或 job 操作使用本 Skill。安装、升级、主机迁移或回滚只由显式调用的
`$pennix-workflow-lifecycle` 处理；跨组件职责不清时改用 `$pennix-workflow-routing`。

## 路由规则

1. 仅当工具 schema 支持批量且已知有多个文本文件时，使用 `inspect_local_file` 的 `files` 批量读取；单一目标或不同视图直接调用对应工具。
2. Trellis Channel 等生命周期等待、交互、Hook、MCP resource 及其他专用协议直接按其原生接口调用，绝不嵌入 `run`。
3. `run` 只承载一条非交互式 CLI；长时操作改用 `run_background`、`job_output`、`job_kill`。已有直接 FastCtx schema 的操作不再包一层 shell，也绝不把 `apply_patch` 传给 `run`。
4. 语义代码编辑使用 Codex `apply_patch`；只有确定性的批量机械替换才使用 FastCtx `replace`，并先 dry-run、设置替换上限。
5. 项目 `AGENTS.md`、项目 spec 和已有专用协议优先；无法判断组件所有权时停止 FastCtx 路由，改用 `$pennix-workflow-routing` 收敛。

FastCtx 不可用时，按项目规则降级到宿主原生工具；不把当前操作输出自动写入任务事实、记忆或 Git。
