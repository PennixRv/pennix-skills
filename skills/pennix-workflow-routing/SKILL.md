---
name: pennix-workflow-routing
description: "Route cross-component Pennix workflow requests by ownership and call semantics across Trellis, context-mode, CodeGraph, Fast Context, web retrieval, Skills, Hook/config, and native tools. Use when a task spans these components or the correct route is unclear; do not use for ordinary single-tool work."
---

# Pennix 工作流路由

## 适用范围

当任务同时涉及多个工作流组件、用户询问组件职责/工具路由，或当前调用的语义无法直接判断时使用本 Skill。它只负责
做路由和边界判断；单个工具已有清晰协议时，直接遵守该工具或对应 Skill 的说明，不为它再包一层路由器。

## 判定顺序

先看调用语义，再看组件名称：

| 调用语义 | 首选路径 | 事实与持久化边界 |
| --- | --- | --- |
| 修改文件、导航、进程控制、短小观察 | 宿主原生工具 | 不额外持久化 |
| 生命周期、事件等待、交互、有限结构化结果或专用错误协议 | 直接调用原工具 | 采用原协议状态，不套 `ctx_execute` |
| 已批准项目的符号、调用关系、架构或影响范围 | CodeGraph | 关键结论回到当前文件核验；未批准项目不得自动启用索引 |
| 本地检索和 CodeGraph 都无法定位的模糊业务、历史或遗留代码位置 | `fast-context` | 只产生候选；必须在当前项目本地核验，默认不持久化 |
| 当前外部资料、网页或多来源研究 | 先 `tavily-hikari`；一次确认不可用后，当前会话的 Codex 原生网络检索 | 外部结果先作为证据候选；核验后才写入任务研究或用户明确指定的持久位置 |
| 测试、日志、长差异、递归检索、构建/依赖输出或大文件分析 | context-mode 聚合 | 默认请求内处理；不要把失败或未经核验的结果写入持久索引 |
| 已有工具支持文件输出的大型结构化结果 | 原工具先写入已批准文件，再用 `ctx_execute_file` 分析 | 不把原始结果重新塞回工具参数 |

无法预判本地文本规模且没有独立协议时，使用 context-mode 聚合；无法判断一个结构化工具是否有界时，先使用其原协议。

## 外部检索降级

- 普通外部检索必须先走 `tavily-hikari`。正确构造的单次 Hikari 操作若因上游/网络错误、配额、超时、
  不可用前置条件、来源导致的命令失败或畸形响应而不可用，再将同一个有界请求交给当前会话的 Codex 原生网络检索。
- 不支持的 CLI 选项、缺少必需参数等可在本地改正的调用/用法错误，先改正调用，不能直接触发降级。
- 降级只用于有界搜索和已知页面读取；原请求为 map、crawl 或 research 时，只能收敛为满足请求所需的
  搜索加页面读取，不宣称具备 Hikari 对应操作的等价语义。
- 整个路由只允许这一次降级：不重试 Hikari、不并行双跑、不改配置、不暴露诊断中的敏感信息、不再选择第三个 provider。
  保留用户、task 或 system 指定的来源、工具、时效、隐私和范围约束，并在对外结果中简要说明路由发生变化。
- 若 Codex 原生网络检索也不可用，报告检索缺口并停止；显式要求特定工具或来源的更高优先级指令始终覆盖本默认规则。

## 组件职责

- `Trellis` 是项目 task、任务文件、跨会话状态和工作节点生命周期的权威；context-mode 不决定项目任务语义。
- 项目 `AGENTS.md` 与 `.trellis/spec/` 保存项目事实、任务合同和项目特殊路由；Skill 不覆盖更近的项目规则。
- `OpenViking` 只承接用户明确要求的外部持久知识；它不是 Trellis 任务事实、当前项目文件或普通会话记忆的替代品。
- CodeGraph 只用于当前项目已经批准的 `.codegraph/` 索引；首次启用或改变索引配置使用 `codegraph-project-setup`，不因普通检索自动初始化，
  linked Git worktree 不使用 CodeGraph。
- `parallel-work` 只为确有独立证据价值的工作准备有界 Trellis 候选请求；`evidence-report` 校验候选报告，`review-gate`
  校验重大候选的独立复核。主会话保留项目事实、验收和 Git，工作节点不实施、不改权威资产、不控制生命周期、不再次派发。
- `trellis-research-record` 将核验后的研究事实、候选、不确定项和下一动作写入当前 task；它不是第二套事实台账。
- `pennix-session-handoff` 只处理用户明确要求的正式交接；`pennix-skills-install` 只处理用户明确要求的组合安装/更新；
  `codex-hook-registration` 只处理审查后的用户级 Hook 片段。不要从普通路由请求推导这些高影响动作的授权。
- Hook/config 和拥有该行为的运行时负责必须发生的事件、阻断、信任、生命周期和审计；提示词只能表达决策原则，不能宣称确定性保证。

## 禁止混淆

- `ctx_search` 只查询已持久化内容和会话记忆，不是在线搜索、实时仓库扫描、CodeGraph 或当前项目事实源。
- CodeGraph、Fast Context、Tavily 和 context-mode 的结果都不能直接成为 task、Issue 或配置事实；先回到当前权威文件核验。
- 不用 context-mode 重实现 Trellis channel watcher、事件等待、Hook 交互或其他已有专用协议；不通过轮询替代生命周期等待。
- 不因“用户希望并行”就自动派发 worker；没有独立证据价值时保留主会话 inline 路径。
- 不将凭据、会话、缓存、数据库、日志、运行态、原始外部响应或未经核验的候选写入 Git 或持久索引。

## 输出

路由结论应简要说明：请求语义、唯一责任组件、是否需要先读项目规则、候选如何核验、是否允许持久化、所需用户授权和
停止条件。若基础工具按正确原生调用仍不可用，保留原错误并停止；外部网络检索仅可按“外部检索降级”使用一次
Codex 原生网络检索，其他路径不要用第二套状态机、替代 provider 或自定义重试掩盖能力缺口。
