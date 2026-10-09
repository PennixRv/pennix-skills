---
name: pennix-workflow-routing
description: "Route cross-component Pennix workflow requests by ownership and call semantics across Trellis, FastCtx, CodeGraph, Windsurf Code Search, web retrieval, Skills, Hook/config, and native tools. Use when a task spans or may span these components, or the correct route is unclear; do not use for ordinary single-tool work."
---

# Pennix 工作流路由

## 适用范围

当任务同时涉及多个工作流组件、用户询问组件职责/工具路由，或当前调用的语义无法直接判断时使用本 Skill。它只负责
做 admission、路由和边界判断；单个工具已有清晰协议时，直接遵守该工具或对应 Skill 的说明，不为它再包一层路由器。

## Admission first

在选择工具或 transport 前，对跨组件请求或 owner 不清的调用完成一次短生命周期
admission；单一工具已有明确 native protocol 时直接遵循，不额外套路由层。不能因为调用
看起来像 `rg`、文件读取或本地 CLI 就跳过 owner 判断。至少判断以下彼此独立的维度，并把
结果写入当前 Trellis task 或返回给调用方：

- `work_domain`：工程/工作流治理、系统 lifecycle 消费、项目 Trellis 资产更新，或普通本地操作；
- `delivery_mode`：受保护目标不变的精确证据交付，或 change-bearing；
- `execution_class`：单 owner、范围和验证都立即可收敛的 direct/lightweight，或 planned；
- `decision_frontier`：是否存在至少一个尚未由既有约定决定的 material decision；
- `approval_mode`：是否已有同一 task、当前封口实质版本、展示最终方案之后的明确实施批准；初始交付请求、父任务批准和设计选项回答不算。

`analysis_only` 只表示受保护目标不变的只读证据交付；复杂度、跨 owner、多证据单元、推荐或未决产品选项都不触发实施批准。明确的研究请求授权主会话完成其证据工作。只有当研究范围/方法依赖尚未回答的用户选择时，才就该选择调用 `$pennix-decision-grill`。用户要求并行 subnode 时，必须先冻结派发方案并获明确批准再 spawn/send；批准仅覆盖列明的证据工作。任何实际变更、部署、发布、凭据或外部运行态动作仍按 change-bearing owner 的原生授权路径处理。

Admission 不是第二套状态机。它只返回 `owner`、`allowed_transport`、`state_writer`、
`exit_conditions` 和 `replan_trigger`；Trellis、lifecycle、FastCtx 及其他 owner 仍各自
维护自己的状态。

除边界明确的只读研究外，先筛选真正由用户决定的实质取舍；单个就绪选择也进入 `$pennix-decision-grill`。其依赖、优先级、分轮与答复记录由该 Skill 负责，不在路由层复制问答过程。执行中的实质歧义立即说明影响并暂停依赖动作；证据工作拉长前先在当前 task 保存决策节点和返回动作，再走对应检索 owner。

## 判定顺序

先做 work-domain 和 native-owner preflight，再看组件名称。工具可用性、名称或工具描述中的通用能力不转移语义 owner：

| 调用语义 | 首选路径 | 事实与持久化边界 |
| --- | --- | --- |
| Trellis task/phase/Channel、formal handoff、Codex 原生交互/Hook、owner MCP/TUI、lifecycle action 或专用错误协议 | 直接调用唯一原生 owner | 采用原协议状态，不套 FastCtx；原生不可用即停止 |
| Grok、Tavily、Windsurf、CodeGraph 或 `openai-docs` 专用检索 | 直接调用对应 retrieval/MCP/API owner | FastCtx 不是 provider、启动器或 fallback |
| 源码、配置、任务文档或其他文本的语义创建/修改 | 宿主原生 `apply_patch` | 不通过 FastCtx 或 shell/Python 写入脚本代写；专用 owner 生成的资产仍走原协议 |
| 普通本地文件、非交互 CLI、构建/测试、递归检索或大输出分析（排除上述语义写入和专用 owner） | FastCtx（按 `$pennix-fastctx-routing`） | 只保存当前操作结果，不额外持久化；机械批量替换先 dry-run 并限定次数 |
| 已配置服务的健康检查、有限查询或读取 | 直接调用当前会话中可用的 MCP 工具 | 若工具未绑定到当前会话，报告能力缺口并停止；不要改走 shell HTTP |
| 已批准项目的符号、调用关系、架构或影响范围 | CodeGraph | 关键结论回到当前文件核验；未批准项目不得自动启用索引 |
| 本地检索和 CodeGraph 都无法定位的模糊业务、历史或遗留代码位置 | `windsurf-code-search` | 只产生候选；必须在当前项目本地核验，默认不持久化 |
| 当前外部资料、网页或多来源研究 | 先 `grok-search`；一次确认不可用后，单次 `tavily-hikari` 自托管辅助路径 | 外部结果先作为证据候选；核验后才写入任务研究或用户明确指定的持久位置 |
| 测试、日志、长差异、递归检索、构建/依赖输出或大文件分析 | FastCtx 有界工具或 job | 默认当前请求/显式 job 处理；不要把结果自动写入任务事实 |
| 已有工具支持文件输出的大型结构化结果 | 原工具先写入已批准文件，再用原生读取或 FastCtx 分页分析 | 不把原始结果重新塞回工具参数 |

无法预判本地文本规模且没有独立协议时，使用 FastCtx 的有界读取、搜索或 job；无法判断一个结构化工具是否有界时，先使用其原协议。判断 FastCtx 是否可用，只依据当前会话暴露的宿主原生工具和对该工具的实际调用结果；`functions.exec` 内嵌编排器的 `ALL_TOOLS` 不是宿主完整工具清单，不能因其中缺少 MCP 名称而判定 FastCtx 不可用。只有宿主当前确实未暴露 FastCtx 原生工具时，普通本地操作才直接降级到宿主原生工具，不重新引入旧的 `ctx_*` 路径。原生调用发生 schema、权限、传输或服务错误时保留实际错误类别，不得把它改写为“工具缺失”。专用 owner 不可用时不允许降级到 FastCtx 或 shell 模拟。

专用 owner 的 executable 仍属于专用 owner：不得使用 `mcp__fastctx.run`、FastCtx
`run_background`/job、`replace`、shell HTTP 或通用 wrapper 启动、转发、重试、轮询、等待
或解释它。正确 native channel 不可用时保留原始能力缺口并停止。只有 owner 已经完成且
产生了批准的普通结果文件时，FastCtx 才能做不推进 owner 状态的读取或分析。

Trellis 的本地 CLI（包括 `task.py`）使用当前宿主原生 shell 工具；Codex 中是
`exec_command`，不是 FastCtx `run`。`task.py current --json` 的 `session_source`
表示身份，`source=unbound_task|unbound_ambiguous` 表示尚未绑定任务，两者分别判断。
有身份时按用户明确意图原生 `select`，再遵守任务阶段；只有正确原生路径仍返回空身份
时才报告宿主身份能力缺口。FastCtx 服务环境没有身份不能证明 Trellis 生命周期 bug，
也不授权复制环境身份、借用其他会话 pointer 或制造 shell ticket。

## 当前 Trellis fork 并行工作流

此段只负责入口分流；Trellis Channel、subnode profile、queue 和 report/disposition 仍是当前 Pennix Trellis beta fork 的唯一执行合同。先确认项目选择的 workflow 和 Trellis 版本，再按以下顺序路由：

1. 普通实现、审查或研究默认由主会话 inline 完成；“并行”措辞本身不构成派发授权。用户明确要求独立证据后，才考虑 subnode；复杂或跨 owner 的只读研究仍可由主会话在 planning 中完成。
2. 只有 change-bearing work 需要其原生 Planning Seal 与实施批准。研究任务的复杂度、跨 owner、依赖分析或建议本身不触发实施门；仅对会实质改变研究范围/方法的用户选择调用 `$pennix-decision-grill`。
3. 显式 subnode 工作先读项目当前 workflow 和 `trellis-channel` 的 `subnode-work` procedure 及多目标派发 reference；首次 spawn/send 前，目标 task 必须包含冻结的研究问题、unit 映射/合并理由、brief 范围与停止条件/报告落点、并行和 FIFO 接受策略，并取得用户明确批准。该批准仅授权列明的 evidence work；实质改变派发方案需重批。inline 不禁止 Channel 独立证据；缺少独立报告不能静默降级成主代理通过结论。本 Skill 不复制 schema、FIFO 或 validator。
4. 多个独立 evidence units 只有在项目可靠性门满足后才进入 FIFO queue。读取项目 `.trellis/agents/subnode-profiles.json`，由 Trellis profile 动态解析模型与 reasoning effort；Skill 不写死映射。仅在证据难度或风险足以说明时选择 `xhigh`。
5. 创建/派发、发送、barrier/wait、队列推进均走 `$trellis-channel` 与当前 fork 的原生 Channel 命令。使用一个原生终态 wait；不得用持续轮询、多个 waiter、自动重试或常驻调度器代替通知/等待合同。
6. Worker 终态只表示执行结束，不等于结果验收。协调者核验报告完整性、引用来源和受保护目标，再写入一次 disposition 后才能推进下一项。
7. Trellis task、Channel、profile、queue、spawn/send、barrier/wait 和状态转换调用必须直达 Trellis owner；不得由 FastCtx 包装、代理、后台 job 化或代为轮询。
8. 临时任务切换用原生 `task.py select` 绑定规划上下文，不能以 start 代替选择或批准。有在途节点时按 Channel procedure 暂停补位、排空所有已派节点与 reservation、保存未派队列和原阶段后再 select；不自动重启用户已停止的任务。普通继续/压缩恢复保持断点快路径。

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

SiYuan 的 `web_search`、`web_fetch`、`http_request` 只服务实际的知识操作，例如用户要求的来源导入或知识整理。独立外部调研、Codex 官方资料检索和本地项目定位仍走各自 owner；不得借用思源网页工具作为通用检索或其他 owner 的 fallback。保留思源全部原生能力，按调用意图限定路由。

知识、历史回溯和规则晋升按用户意图选择唯一主要来源，见
[`references/knowledge-promotion.md`](references/knowledge-promotion.md)。已配置思源的人工知识操作由
`pennix-siyuan-memory` 使用原生 MCP；当前 task/源码/spec、`trellis mem` 历史和 formal handoff
各保留自身 owner。知识失败不阻断任务或交接，禁止无条件预加载、自动捕获与双向同步。

- `Trellis` 是项目 task、任务文件、跨会话状态和工作节点生命周期的权威；FastCtx 不决定项目任务语义。正式 handoff 的 `source.rollout.session_id` 只是来源 provenance；目标绑定只能来自当前 Trellis 直接解析的 `source=session:<target-key>`，不能把旧 session 或 `session-fallback:<key>` 当作目标。
- 项目 `AGENTS.md` 与 `.trellis/spec/` 保存项目事实、任务合同和项目特殊路由；Skill 不覆盖更近的项目规则。
- CodeGraph 只用于当前项目已经批准的 `.codegraph/` 索引；首次启用或改变索引配置由 `$pennix-workflow-lifecycle` 的 CodeGraph deployment adapter 计划并执行，不因普通检索自动初始化，
  linked Git worktree 不使用 CodeGraph。
- 确有独立证据价值的工作遵循当前项目选择的 Trellis `subnode` procedure。Trellis 维护其 brief、持久化报告和
  Channel 生命周期；主会话保留项目事实、验收和 Git，不把该合同复制为用户级 Skill。
- 已初始化 Trellis 项目的 bundled `trellis-research-record` 将核验后的研究事实、候选、不确定项和下一动作写入当前 task；它不是第二套事实台账。
- 已初始化项目的 Trellis 资产更新和已选 workflow 刷新由 `$pennix-trellis-project-update` 负责，必须调用当前 Trellis fork 的原生 `trellis update` / `trellis workflow`；系统级组件部署仍由 `$pennix-workflow-lifecycle` 负责，`workflow-doctor` 只做只读诊断。
- `pennix-session-handoff` 只处理用户明确要求的正式交接；其 immutable core、append-only lifecycle receipt 和确定性 retention 归它所有，但不拥有 Trellis task/pointer。对带 task 的新协议，Skill 只编排 Trellis 原生 `ownership quiesce|seal|retire|claim|consume|archive`，不得自行写 pointer；正式交接通过本地来源封口和配对包验证记录来源收敛。初始 admission 只在 core、prompt、`$trellis-start` 和当前事实完整核对后记录一次 `reconciled`，不完整消费不写 target reservation；后续 `claim` 必须有新的明确继续授权。组件部署、Skills 物化、CodeGraph project prepare、FastCtx 更新和审查后的用户级 Hook 片段统一由 `$pennix-workflow-lifecycle` 的对应 deployment adapter 规划；不要从普通路由请求推导这些高影响动作的授权。
- Hook/config 和拥有该行为的运行时负责必须发生的事件、阻断、信任、生命周期和审计；提示词只能表达决策原则，不能宣称确定性保证。

## 禁止混淆

- FastCtx 的文件、搜索和 job 结果只描述当前操作；任务事实和授权应回到 Trellis/Git 与当前用户指令核验。
- CodeGraph、Windsurf Code Search、Tavily 和 FastCtx 的结果都不能直接成为 task、Issue 或配置事实；先回到当前权威文件核验。
- 不用 FastCtx 重实现 Trellis channel watcher、事件等待、Hook 交互或其他已有专用协议；不通过轮询替代生命周期等待。
- `grok-search` 是外部检索 owner，不是 FastCtx 的 provider 或 adapter；只有用户确实需要当前外部资料时才按它自己的 Skill 调用。FastCtx 不能把它的网络调用、credential path、provider fallback 或错误协议收纳为本地 job。
- `openai-docs` 只拥有其允许的 OpenAI/Codex/API/ChatGPT 官方资料路径；它与 Grok-first 外部检索是两个独立 owner，均不得通过 FastCtx 启动或代理。
- 任何改变、确认、等待、重试、轮询或解释专用 owner 状态的本地命令，仍是 owner 调用而不是普通本地 CLI；FastCtx 只能读取 owner 完成后的普通结果。
- 不因“用户希望并行”就自动派发 worker；没有独立证据价值时保留主会话 inline 路径。
- 不将凭据、会话、缓存、数据库、日志、运行态、原始外部响应或未经核验的候选写入 Git 或持久索引。

## 输出

路由结论应简要说明：请求语义、唯一责任组件、是否需要先读项目规则、候选如何核验、是否允许持久化、所需用户授权和
停止条件。若基础工具按正确原生调用仍不可用，保留原错误并停止；外部网络检索仅可按“外部检索降级”使用一次
自托管 Tavily 路径，其他路径不要用第二套状态机、替代 provider 或自定义重试掩盖能力缺口。
