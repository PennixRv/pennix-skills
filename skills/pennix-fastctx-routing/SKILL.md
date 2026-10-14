---
name: pennix-fastctx-routing
description: 为本地文件读取、搜索、普通非交互命令和后台任务选择 FastCtx 工具。排除语义编辑、Trellis 任务与 Channel、外部检索和组件部署，遵守各自原生接口。
---

# FastCtx 本地操作路由

## 适用范围

本地文件读取、搜索、普通非交互命令、构建、测试和后台任务使用本 Skill，不要求用户先点名 FastCtx。安装、升级、主机迁移和回滚由 `$pennix-component-lifecycle` 处理；跨组件职责不清时用 `$pennix-workflow-routing`。

先按操作语义区分普通本地操作与组件规定的调用。可执行文件位于本地、调用形式是 shell 或输出是 JSON，都不改变接口要求。

| 操作 | 规定入口 |
|---|---|
| 源码、配置、任务文档等文本的语义创建或修改 | 宿主原生 `apply_patch`；组件生成的资产仍由其生成接口写入 |
| Trellis 任务状态、绑定、`task.py`、Channel 子节点与等待 | Trellis 原生接口；`task.py` 在 Codex 中通过 `exec_command` 调用 |
| 正式交接、Hook 事件/诊断、原生 Plugin/MCP/TUI 和用户提问 | 对应组件或宿主规定的接口；用户提问用原生 `request_user_input` |
| `$pennix-grok-search`、`$pennix-tavily-search`、`$pennix-windsurf-code-search`、CodeGraph 和官方文档检索 | 各检索工具规定的命令、MCP 或 API 入口 |
| 系统组件安装、配置、验证和集合替换 | `$pennix-component-lifecycle` 及其指定的原生安装工具 |

上述操作不转交 FastCtx，即使最终涉及本地文件、命令或等待。规定接口不可用或调用被拒绝时，保留真实错误并停止相关动作，不用 FastCtx、轮询、shell HTTP 或文件替换模拟协议。

## 参数契约

只使用 FastCtx `tools/list` 发布的规范字段，不增加或猜测别名：`inspect_local_file` 单文件顶层使用 `file_path`，批量条目使用 `path`；`grep` 使用必填 `pattern`；`run` 使用 `command`、`cwd`、`timeout_ms`、`login_shell` 和 `encoding`。出现 `failed to deserialize parameters` 时先核对工具名、字段位置和规范 schema，修正调用来源后再继续；不把合法参数错误改报为容量不足，也不静默重跑具有副作用的命令。

## 路由规则

工具可用性以当前会话宿主实际声明和真实调用结果为准。`functions.exec` 中的嵌套编排器 `ALL_TOOLS` 只列出可供该编排器调用的嵌套工具，不是宿主原生 MCP 清单，也不是宿主全部工具清单；缺少 FastCtx 名称只能说明不能从该嵌套调用面调用，不能证明宿主直接面未暴露、FastCtx 未安装或不可用。宿主实际暴露的 FastCtx 工具可直接调用，也可通过实际暴露它的原生编排器调用。仅在核对当前宿主声明后，确认规定的有效入口未暴露或不可用时，普通本地操作才按既有规则降级；不能只查 `ALL_TOOLS` 得出缺失结论。调用已暴露工具遇到 schema、权限、传输或服务错误时保留原错误类别，不得改报为工具缺失。

FastCtx 的单次输出预算耗尽、可恢复的分页限制和外层编排结果截断都不是工具缺失，也不结束当前工作。先按实际结果收窄路径、搜索范围或页大小；Partial 只按结果给出的精确 offset/files/after_seq 续读，容量耗尽时在当前工作中继续推进，不等待新的用户轮次，也不忙循环重放同一请求。`run` 已执行副作用时不得盲目重跑；应使用安全检查、已有日志或显式重定向。容量提示不触发 shell fallback、不关闭 provider 保护、不擅自扩大预算；合理有界调用仍频繁受限时，记录实际证据交 FastCtx owner 评估配置，不宣称本 Skill 能修改服务容量。

1. 排除上表操作后，普通本地读取、搜索、非交互命令、构建、测试和后台任务使用 FastCtx。
2. 仅当工具 schema 支持批量且已知有多个文本文件时，使用 `inspect_local_file` 的 `files` 批量读取；单一目标或不同视图直接调用对应工具。
3. `run` 用于普通非交互 CLI；长时操作改用 `run_background`、`job_output`、`job_kill`。已有 FastCtx schema 的文件操作不再包一层 shell，也绝不把 `apply_patch` 传给 `run`。
4. 语义编辑不通过 `run`、`run_background` 或 shell/Python 写入脚本代写。只有确定性的批量机械替换才使用 FastCtx `replace`，先预览并设置替换上限。
5. 检索工具完成调用并产生已批准的普通本地结果文件后，FastCtx 可以读取或分析该文件；不得调用、代替或推进检索协议。
6. 项目 `AGENTS.md`、项目规范和已有组件协议优先；无法确定规定接口时停止 FastCtx 路由，改用 `$pennix-workflow-routing`。

独立调用可以按宿主原生机制批量编排；读取多个已知文本仍优先使用 `inspect_local_file.files`。保留每个结果的内容、错误与 Complete/Partial 续读参数。聚合截断时先用有界直接调用补回，不能宣称已经读完；依赖前页 offset 的续读顺序执行。调用形式不会改变职责或授予新的协议权限。

上表组件的命令禁止通过 FastCtx `run`、`run_background`、后台任务、`replace`、shell HTTP 或通用包装器启动、转发、重试、轮询、等待或解释。规定入口不可用时保留 `blocked`/`capability-gap` 结果，不用结果文件读取确认或模拟组件状态。

FastCtx 经上述证据确认不可用时，按项目规则降级到宿主原生工具；schema、权限、传输、服务、容量或命令失败仍按实际错误和原生合同处理，不自动降级。不把当前操作输出自动写入任务事实、记忆或 Git。

若误将 `task.py` 交给 FastCtx 后发生身份缺失，先纠正调用为当前宿主原生 shell
（Codex 的 `exec_command`），再用原生 `current --json` 区分身份与绑定：
`session_source` 非空表示身份存在，`unbound_task` / `unbound_ambiguous` 只表示没有
活动任务绑定。按用户明确意图原生 `select`，不把它当作实施批准。正确原生路径仍无身份
才报告能力缺口；不向 FastCtx 注入复制/猜造的身份，不手写 pointer 或 shell ticket。
