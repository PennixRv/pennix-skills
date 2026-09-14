---
name: pennix-workflow-routing
description: "Route cross-component Pennix workflow requests by ownership and call semantics across Trellis, FastCtx, CodeGraph, Windsurf Code Search, OpenViking, web retrieval, Skills, Hook/config, and native tools. Use when a task spans or may span these components, or the correct route is unclear; do not use for ordinary single-tool work."
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
| 生命周期、事件等待、交互、有限结构化结果或专用错误协议 | 直接调用原工具 | 采用原协议状态，不套 FastCtx |
| 已配置服务的健康检查、有限查询或读取 | 直接调用当前会话中可用的 MCP 工具 | 若工具未绑定到当前会话，报告能力缺口并停止；不要改走 shell HTTP |
| 已批准项目的符号、调用关系、架构或影响范围 | CodeGraph | 关键结论回到当前文件核验；未批准项目不得自动启用索引 |
| 本地检索和 CodeGraph 都无法定位的模糊业务、历史或遗留代码位置 | `windsurf-code-search` | 只产生候选；必须在当前项目本地核验，默认不持久化 |
| 当前外部资料、网页或多来源研究 | 先 `grok-search`；一次确认不可用后，单次 `tavily-hikari` 自托管辅助路径 | 外部结果先作为证据候选；核验后才写入任务研究或用户明确指定的持久位置 |
| 测试、日志、长差异、递归检索、构建/依赖输出或大文件分析 | FastCtx 有界工具或 job | 默认当前请求/显式 job 处理；不要把结果自动写入 OpenViking 或任务事实 |
| 已有工具支持文件输出的大型结构化结果 | 原工具先写入已批准文件，再用原生读取或 FastCtx 分页分析 | 不把原始结果重新塞回工具参数 |

无法预判本地文本规模且没有独立协议时，使用 FastCtx 的有界读取、搜索或 job；无法判断一个结构化工具是否有界时，先使用其原协议。FastCtx 不可用时直接降级到宿主原生工具，不重新引入旧的 `ctx_*` 路径。

## 本地证据优先

- 涉及当前机器、当前项目、工作树、源码、配置、日志或已存在资源时，先使用本地文件工具、宿主原生工具和已批准的 CodeGraph；本地检索到足以回答问题的证据后，不启动 `grok-search`、`tavily-hikari` 或 `windsurf-code-search`。
- 本地存在目标源码但问题要求当前上游状态、公开资料、跨项目比较或外部事实时，才进入外部检索；外部检索结果仅补充或对照本地证据，不能替代本地事实核验。
- 本地检索结果为空、过时、无法解释，或用户明确要求外部来源时，按上表进入对应外部路径；用户明确指定的来源优先于本默认顺序，但仍不改变任务和凭据边界。
- `grok-search` Skill 的可发现性不构成自动调用理由；调用前必须先判断问题是否确实需要外部资料。

## 外部检索降级

- 普通外部检索必须先走 `grok-search`。正确构造的单次 Grok
  操作若因上游/网络错误、配额、超时、不可用前置条件、来源导致的命令失败或
  畸形响应而不可用，才将同一个有界请求交给自托管 `tavily-hikari` 一次。
- 不支持的 CLI 选项、缺少必需参数等可在本地改正的调用/用法错误，先改正调用，不能直接触发降级。
- 降级只用于有界搜索和已知页面读取；原请求为 map、crawl 或 research 时，只能收敛为满足请求所需的
  搜索加页面读取，不宣称具备原路径的等价语义。
- 整个路由只允许这一次降级：不重试、不并行双跑、不改配置、不暴露诊断中的敏感信息、不再选择第三个 provider。
  保留用户、task 或 system 指定的来源、工具、时效、隐私和范围约束，并在对外结果中简要说明路由发生变化。
- 若自托管 Tavily 路径也不可用，报告检索缺口并停止；显式要求特定工具或来源的更高优先级指令始终覆盖本默认规则。

## 组件职责

- `Trellis` 是项目 task、任务文件、跨会话状态和工作节点生命周期的权威；FastCtx 不决定项目任务语义。正式 handoff 的 `source.rollout.session_id` 只是来源 provenance；目标绑定只能来自当前 Trellis 直接解析的 `source=session:<target-key>`，不能把旧 session 或 `session-fallback:<key>` 当作目标。
- 项目 `AGENTS.md` 与 `.trellis/spec/` 保存项目事实、任务合同和项目特殊路由；Skill 不覆盖更近的项目规则。
- `OpenViking` 承接工作期语义 recall、经验检索和用户明确要求的持久知识；它不是 Trellis 任务事实、当前项目文件或普通会话控制的替代品。
- CodeGraph 只用于当前项目已经批准的 `.codegraph/` 索引；首次启用或改变索引配置使用 `codegraph-project-setup`，不因普通检索自动初始化，
  linked Git worktree 不使用 CodeGraph。
- 确有独立证据价值的工作遵循当前项目选择的 Trellis `subnode` procedure。Trellis 维护其 brief、持久化报告和
  Channel 生命周期；主会话保留项目事实、验收和 Git，不把该合同复制为用户级 Skill。
- 已初始化 Trellis 项目的 bundled `trellis-research-record` 将核验后的研究事实、候选、不确定项和下一动作写入当前 task；它不是第二套事实台账。
- `pennix-session-handoff` 只处理用户明确要求的正式交接；其 immutable core、append-only lifecycle receipt 和精确 retention 归它所有，但不拥有 Trellis task/pointer。对带 task 的新协议，Skill 只编排 Trellis 原生 `ownership quiesce|seal|retire|claim|consume|archive`，不得自行写 pointer；初始 admission 仍只核对并停止，后续 `claim` 必须有新的明确继续授权。`pennix-skills-install` 只处理用户明确要求的组合安装/更新；
  `codex-hook-registration` 只处理审查后的用户级 Hook 片段。不要从普通路由请求推导这些高影响动作的授权。
- Hook/config 和拥有该行为的运行时负责必须发生的事件、阻断、信任、生命周期和审计；提示词只能表达决策原则，不能宣称确定性保证。

## 禁止混淆

- FastCtx 的文件、搜索和 job 结果只描述当前操作，不是 OpenViking 记忆、实时任务事实或授权；需要长期语义记忆时走 OpenViking，需要任务事实时回到 Trellis/Git。
- CodeGraph、Windsurf Code Search、Tavily 和 FastCtx 的结果都不能直接成为 task、Issue 或配置事实；先回到当前权威文件核验。
- 不用 FastCtx 重实现 Trellis channel watcher、事件等待、Hook 交互或其他已有专用协议；不通过轮询替代生命周期等待。
- 不因“用户希望并行”就自动派发 worker；没有独立证据价值时保留主会话 inline 路径。
- 不将凭据、会话、缓存、数据库、日志、运行态、原始外部响应或未经核验的候选写入 Git 或持久索引。
- handoff 的 OpenViking observation 只能作为有界、已验证的 source convergence 证据；OpenViking/MCP 不写本地 core、Trellis task 或 receipt truth，也不通过 shell HTTP 绕过官方工具路由。没有对应 exact-read proof 时保持 `core_only` 或报告 `pending|unsupported|unavailable`。
- 活动 task 的工作期记忆：先使用官方 Plugin 已注入的 recall；历史称谓、复杂多步工作、相似故障或跨会话上下文需要深入时，使用 `ov-experience-memory` 的 `find/search`，再对关键 URI `read`。只有实际改变后续理解或行动的目标、约束、决定、否决、验证、经验、阻塞或待办才登记到 task-scoped research note。FastCtx 的当前操作输出不自动登记记忆。
- 工作期语义登记使用 `pennix-worktime-memory`；它不复制 transcript、不替代官方 capture/commit、不创建 scheduler 或本地 memory ledger。用户明确要求长期记忆或形成稳定跨任务偏好/经验时，才调用官方 `remember/write`；OpenViking 不可用时只降级记忆增强，不阻断 Trellis、Git 或普通实施。

## 输出

路由结论应简要说明：请求语义、唯一责任组件、是否需要先读项目规则、候选如何核验、是否允许持久化、所需用户授权和
停止条件。若基础工具按正确原生调用仍不可用，保留原错误并停止；外部网络检索仅可按“外部检索降级”使用一次
自托管 Tavily 路径，其他路径不要用第二套状态机、替代 provider 或自定义重试掩盖能力缺口。
