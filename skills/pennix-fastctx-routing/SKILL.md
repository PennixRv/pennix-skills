---
name: pennix-fastctx-routing
description: 为本地文件读取、搜索、普通非交互命令和后台任务选择 FastCtx 工具。排除语义编辑、Trellis 任务与 Channel、外部检索和组件部署，遵守各自原生接口。
---

# FastCtx 本地操作路由

## 默认路径

FastCtx 是普通本地读取、搜索、非交互命令、构建、测试和后台任务的默认入口，不要求用户点名。优先使用其原生文件与搜索工具，利用有界返回和 Complete/Partial 续读信息控制上下文、核对已读范围；外层编排仍可能截断，调用者须检查结果完整性。

首次读取 `AGENTS.md`、Skill、规范和任务文档也适用；开始新任务或从原生命令切回普通读取时，按当前动作重新选择入口，不重复整套启动核验。安装、升级、主机迁移和回滚由 `$pennix-component-lifecycle` 处理；职责不清时用 `$pennix-workflow-routing`。

## 逐动作分流

按操作语义区分普通本地操作与组件原生调用。例外只适用于对应动作：读取 PRD 用 FastCtx，`task.py current` 用宿主原生入口，修改 PRD 用 `apply_patch`。同轮含有原生命令，不豁免其他文件读取，也不将二者合并为包含 `cat` 等读取动作的宿主 shell。可执行位置、shell 形式或 JSON 输出不改变接口归属。

| 操作 | 规定入口 |
|---|---|
| 源码、配置、任务文档等文本的语义创建或修改 | 宿主原生 `apply_patch`；组件生成的资产仍由其生成接口写入 |
| Trellis 任务状态、绑定、`task.py`、Channel 子节点与等待 | Trellis 原生接口；`task.py` 在 Codex 中通过 `exec_command` 调用 |
| 正式交接、Hook 事件/诊断、原生 Plugin/MCP/TUI 和用户提问 | 对应组件或宿主规定的接口；用户提问用原生 `request_user_input` |
| `$pennix-grok-search`、`$pennix-tavily-search`、`$pennix-windsurf-code-search`、CodeGraph 和官方文档检索 | 各检索工具规定的命令、MCP 或 API 入口 |
| 系统组件安装、配置、验证和集合替换 | `$pennix-component-lifecycle` 及其指定的原生安装工具 |

上表操作不通过 FastCtx `run`、`run_background`、`replace`、shell HTTP 或通用包装器启动、转发、重试、轮询、等待或解释。规定入口不可用或被拒绝时保留真实错误与 `blocked`/`capability-gap`，停止相关动作。组件操作完成后，FastCtx 可以读取获准的普通结果文件，但不能据此确认或模拟组件状态。

普通本地操作按以下入口执行：

- 已有原生文件或搜索工具时直接使用；schema 支持且已知多个文本文件时，优先用 `inspect_local_file.files` 批量读取，单一目标直接读取，不再包一层 shell。
- 普通非交互 CLI 用 `run`；长时操作用 `run_background`、`job_output`、`job_kill`。
- 语义编辑走 `apply_patch`，不交给 FastCtx 或 shell/Python 写入脚本。确定性的批量机械替换才用 `replace`，先预览并设置替换上限。

项目 `AGENTS.md`、规范和组件协议优先；无法确定规定接口时停止相关 FastCtx 动作，转 `$pennix-workflow-routing`。输出不自动写入任务事实、记忆或 Git。

## 可用性与失败处理

核对宿主实际声明的调用入口：FastCtx 可直接调用，也可通过实际暴露同一 MCP 的宿主原生编排器调用。`functions.exec` 的 `ALL_TOOLS` 仅列出嵌套调用面，缺项不能证明宿主直接工具不存在或 FastCtx 不可用；编排形式不改变组件职责。

只有核对宿主声明并确认没有规定的有效 FastCtx 入口后，普通本地操作才按项目规则降级到宿主原生工具，不恢复旧 `ctx_*` 路径。入口未暴露、宿主未绑定、参数校验、权限、传输或服务错误及命令失败按真实回执分别处理，调用失败不改报为工具缺失，也不自动触发后备路径；容量和截断按下节继续处理。

若误将 `task.py` 交给 FastCtx 后出现身份缺失，先改用宿主原生 shell；身份与绑定的恢复按 [`pennix-workflow-routing`](../pennix-workflow-routing/SKILL.md) 的 Trellis 说明处理，不注入复制或猜造的身份，不手写 pointer 或 shell ticket。

## 参数契约

只使用 FastCtx `tools/list` 发布的规范字段，不猜测别名：`inspect_local_file` 单文件顶层使用 `file_path`，批量条目使用 `path`；`grep` 使用必填 `pattern`；`run` 使用 `command`、`cwd`、`timeout_ms`、`login_shell` 和 `encoding`。出现 `failed to deserialize parameters` 时先核对工具名、字段位置和 schema，修正调用来源；参数错误不改报为容量不足。

## 输出与续读

独立调用可按宿主原生机制并行；保留每个结果的内容、错误与 Complete/Partial 续读参数。依赖前页参数的续读顺序执行，Partial 只按结果给出的精确 offset/files/after_seq 继续；聚合截断时先用有界直接调用补回，未补全不宣称已经读完。

输出预算耗尽、可恢复分页限制或外层截断时，按实际结果收窄路径、搜索范围或页大小，在当前工作中继续，不等待新用户轮次，也不忙循环重放同一请求。容量提示不触发 shell 后备、不关闭 provider 保护或擅自扩大预算；合理有界调用仍频繁受限时，记录证据交 FastCtx owner 评估配置。

`run` 已执行副作用时不得盲目重跑；应使用安全检查、已有日志或显式重定向确认结果。
