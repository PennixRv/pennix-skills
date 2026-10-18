---
name: pennix-context-mode-integration
description: 为本地检索、非交互命令和大输出分析选择 Context Mode；区分全文证据、索引及摘要，保留宿主原生交互、长任务和敏感数据边界。不负责安装或组件状态。
---

# Context Mode 集成

本地检索、构建、测试和大输出分析优先使用宿主声明的 context-mode MCP。工具名称、参数和限制以当前工具帮助为准；不要仅因一个编排入口未暴露工具或一次调用失败而判定宿主缺少工具。没有有效入口时使用宿主原生工具并报告缺口；参数、权限、传输和业务失败按原始回执处理。

## 选择载体

| 操作 | 入口与边界 |
| --- | --- |
| 本地文件处理、检索、非交互命令 | `ctx_execute`、`ctx_execute_file`；代码只返回需要的结果，保留路径与范围 |
| 多个独立命令的大输出检索 | `ctx_batch_execute`；输出会建立索引，仅用于允许持久化的内容 |
| 明确来源的主动索引与检索 | `ctx_index`、`ctx_search`；保留来源，命中与摘要不表示已读全文 |
| Skill、AGENTS、规范、交接必读视图及精确编辑依据 | 宿主原生有界读取，按该入口续页直至完整；不以摘要、搜索片段或索引替代全文 |
| 语义编辑、宿主 MCP、图像/PDF 视觉、request_user_input、实时 continuation | 各自原生入口；不通过执行器模拟或转发宿主总线 |
| 长任务、交互和跨轮后台执行 | 宿主原生执行会话；Codex 的 ctx background 不是持久 Job，不能据此承诺重启后续接 |
| 凭据读写/导入、Windsurf 未核验候选等禁止持久化内容 | 原生入口并遵守对应 owner；不进入自动索引、Hook 正文采集或恢复材料 |

普通 Trellis、Grok、CodeGraph、lifecycle CLI 可以经 Context Mode 执行同一命令，但必须保持 cwd、原生线程身份、参数、退出码、授权、状态和来源；不能用 echo 或自造 JSON 替代调用。部署、发布和其他高影响动作仍需原本授权。短机器回执完整保留；身份无法核验、期限或权限无法等价承载时改走宿主入口，不复制或猜造其他会话身份。

Trellis Channel 的宿主 continuation 按当前项目的排他等待合同执行；等待期间不启动其他工具。普通 CLI 载体能力不授权后台化、并发相关写入或轮询代替原生等待。

## 结果与数据

- 区分进程退出、工具 envelope、业务状态、timeout、取消和部分输出；外层成功不代表命令成功。输出被截断时收窄范围，或沿原生入口的实际 offset 续读，不重复无界调用。
- `ctx_fetch_and_index` 会持久化网页；它不是 Grok、官方文档或其他来源合同的替代入口。网络检索仍按对应 Skill 选择来源、凭据和后备。
- 自动恢复材料属于历史证据，不覆盖当前指令、用户授权及 Trellis/Git 事实。Context Mode 不读取 Codex 独立长期 memory，也不是工作流记忆权威。
- 默认组件数据根为 `${CODEX_HOME:-$HOME/.codex}/context-mode`；显式 `CONTEXT_MODE_DIR` 须为绝对路径。不扫旧目录、不搬迁其他 owner 数据。有限字段处理不保证任意文本脱敏。
- 自动会话派生数据按最近活动保留 30 天，普通主动索引与 Codex 原始历史保留。显式清除使用 `ctx_purge`，必须声明 `confirm: true` 和 `scope: "session"` 或 `scope: "project"`；session 仅指当前核验线程。普通卸载保留数据并报告。

安装、固定版本、MCP 与六 Hook 归属由 `$pennix-component-lifecycle` 导航到独立 `pennix` 工具；不叠加 Codex plugin，不运行组件自更新。跨组件不清时用 [`pennix-workflow-routing`](../pennix-workflow-routing/SKILL.md)。
