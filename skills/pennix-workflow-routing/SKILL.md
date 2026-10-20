---
name: pennix-workflow-routing
description: "按职责与调用语义路由跨组件工作流请求，区分 Trellis、context-mode、CodeGraph、Windsurf Code Search、网页检索、Skill、Hook 和宿主原生工具。用于涉及多个组件或职责不清的请求，不用于普通单工具操作。"
---

# 跨组件工作流路由

## 适用范围

任务涉及多个工作流组件、用户询问职责或工具路由，或调用语义无法直接判断时使用本 Skill。它只判断范围、职责和规定接口；单个工具已有清晰协议时直接遵守，不再增加路由层。

## Skill 身份与路径

加载 Skill 前，先从当前宿主清单找到对应逻辑入口，取得该项的声明路径；短路径只按宿主映射展开根别名，保留剩余目录层级并原样读取，不从 Skill 名称反推目录。项目 Skill 可能位于 `.agents/skills/<skill-name>/SKILL.md`，用户级主集合和 extra 可能分别位于 `skills/pennix-skills/<skill-name>/SKILL.md` 与 `skills/pennix-skills-extra/<skill-name>/SKILL.md`；这些例子不替代本轮声明，也不是依次重试的候选表。Skill 的相对引用以实际加载文件所在目录为基准。若无法确认实际路径，保留原始回执并停止，不通过平铺路径重试，也不因路径猜测失败判定 Skill 或宿主工具不存在。

## 调用前判定

跨组件请求或接口不清时，先判断请求和交付范围，再选择工具。单个工具已有明确协议时直接遵守；执行载体不改变负责组件。将必要判断写入当前任务或返回调用方：

- `work_domain`：工程/工作流治理、系统部署、项目 Trellis 资产更新或普通本地操作；
- `delivery_mode`：受保护目标不变的精确证据交付，或 change-bearing；
- `execution_class`：负责组件、范围和验证都可立即确定的 `direct`，或需要完整方案的 `planned`；
- `decision_frontier`：是否存在尚未由既有约定决定的重要用户取舍；
- `approval_mode`：是否已有针对同一 task 最终展示方案的明确实施批准；“封口并批准推进”可一次授权随后对相同方案原生 seal/approve/start。实质变化须重新展示确认；初始交付请求、父任务批准和普通设计选项回答不算，已有充分授权不重复询问。

`analysis_only` 表示受保护目标不变的只读证据交付；复杂度、跨组件、多证据单元、推荐或未决产品选项本身不触发实施批准。明确研究请求授权主会话完成证据工作；研究范围或方法依赖尚未回答的用户选择时，再调用 `$pennix-decision-grill`。并行子节点先冻结派发方案并获明确批准，再调用 `spawn/send`；批准只覆盖列明的证据工作。实际变更、部署、发布、凭据或外部运行态动作仍按负责组件的变更授权流程处理。

判定结果中的 `owner` 表示负责该操作并规定调用接口的组件，`allowed_transport` 表示允许入口，`state_writer` 表示状态写入组件，`exit_conditions` 和 `replan_trigger` 表示停止与重新规划条件。源码维护仓库、安装工具和状态写入组件可能不同，应分别说明，不能以宽泛代称混为一谈。这不是第二套状态机，各组件仍维护自己的状态。

除有界只读研究外，先筛选重要用户取舍；一个就绪选择也可进入 `$pennix-decision-grill`。渐进问答由该 Skill 负责。执行中出现实质未决选择时，说明影响并暂停依赖动作；拉长证据工作前先保存决策节点和返回动作，再调用规定的检索入口。

## 判定顺序

先看操作语义和规定接口，再看工具名称。工具可用性、位置或通用能力不改变组件职责：

| 调用语义 | 首选路径 | 事实与持久化边界 |
| --- | --- | --- |
| Trellis 任务/阶段、组件 CLI 与系统部署 | 使用 owner 的真实命令和接口；符合当前调用语义时可由 Context Mode 执行并分析回执 | Context Mode 不接管 owner 协议、状态写入或授权；不以 shell 模拟专属协议 |
| Channel continuation、Codex 交互/Hook、原生 MCP/TUI | 对应宿主或组件原生入口 | 保留实时状态与排他等待，不包装宿主总线 |
| 宿主工具面与 Hook 路由核验 | 分别检查宿主 MCP、`functions` 内嵌工具、Context Mode `tools/list` 和 `PreToolUse` matcher/decision | 逐层记录声明、发现、可调用和回执；不以任一层推断其他层 |
| Grok、Tavily、Windsurf、CodeGraph 或 `openai-docs` 检索 | 按来源 Skill 使用发现工具；返回资料可由 Context Mode 处理或按来源合同索引 | 载体不接管来源、凭据、认证输出或降级；未核验候选保留来源和状态 |
| 源码、配置、任务文档等文本的语义创建/修改 | 宿主原生 `apply_patch` | 不通过执行器或 shell/Python 写入脚本代写；生成资产仍由其生成接口写入 |
| 自定义中文技术文档的撰写、改写、校对或审阅 | `$pennix-chinese-tech-writing`，按内容加载参考 | 新增技术文档默认中文，明确语言要求除外；Trellis 原生机械惯例优先，编辑、任务状态和保存仍走各自接口 |
| 日常答复、复杂交付或批准前方案展示需要检查覆盖、详略、重点、结构或图表关系 | `$pennix-agent-output-quality`；中文技术内容再组合 `$pennix-chinese-tech-writing` | 输出质量 Skill 负责内容组织和语义复核，语言 Skill 负责中文表达与保真；简单事实走短路径，不改变任务状态、批准或安装 owner |
| 普通本地文件、非交互命令、构建/测试、递归检索或大输出分析 | 默认按 `$pennix-context-mode-integration` 在 Context Mode 内完成本地数据处理，并按其有限负面边界选载体 | 完整读取必须实际取得全文；索引不证明内容已读或已核验；无固定命令数门槛 |
| 已配置服务的健康检查、有限查询或读取 | 直接调用当前会话中可用的 MCP 工具 | 若工具未绑定到当前会话，报告能力缺口并停止；不要改走 shell HTTP |
| 已批准项目的符号、调用关系、架构或影响范围 | CodeGraph | 关键结论回到当前文件核验；未批准项目不得自动启用索引 |
| 本地检索和 CodeGraph 都无法定位的模糊业务、历史或遗留代码位置 | `$pennix-windsurf-code-search` | 搜索只产生候选；可由 Context Mode 带来源和“未核验”状态处理或索引，作为事实使用前核验当前源码 |
| 当前外部资料、网页或多来源研究 | 先 `$pennix-grok-search`；一次确认不可用后，单次 `$pennix-tavily-search` 自托管辅助路径 | 来源 owner 保留发现和认证合同；已取得资料可由 Context Mode 按来源合同处理/索引，写入任务事实前仍核验 |
| 长任务或跨轮后台执行 | 按需选择可保留所需运行语义的真实执行接口 | 任务时长本身不排除 Context Mode；需要宿主交互或当前接口无法续接时走对应宿主入口 |
| 已有工具支持文件输出的大型结构化结果 | 原工具先写入已批准文件，再用 context-mode 限定分析或原生分页读取 | 不把原始结果重新塞回工具参数，分析结果不自动晋升为任务事实 |
| 工作流缓存、Channel、输出、备份或历史资源的盘点与清理 | `$pennix-resource-cleanup`，再转资源 owner 的原生清理入口 | 默认只读；精确预览和明确授权后才允许 owner 执行 |
| 项目 AGENTS 来源、内部生成块、内容职责或冲突 | `$pennix-project-agents-governance` | 默认只读，手工正文按请求编辑，生成块委托原生 owner |

工具参数、完整读取、输出与数据边界遵守 [`pennix-context-mode-integration`](../pennix-context-mode-integration/SKILL.md)。owner 决定操作语义、权限和状态；其真实非交互命令可由 Context Mode 承载，前提是本次所需身份、参数、退出码与回执均可保留。不得用 shell HTTP、自造 JSON、后台化或代理轮询替代组件协议。

只有两类情形要求改用真实宿主接口：调用本身必须使用宿主专属协议（例如 `apply_patch`、用户审批、宿主 MCP、视觉渲染或实时 continuation）；或证据表明当前 Context Mode 接口无法保留本次实际需要的身份、交互、取消或续接语义。权限拒绝必须遵守，不能换载体绕过。发现错误、未测试、一次失败、文件名、敏感标签、项目外路径、命令副作用、Git、任务时长和候选未核验状态都不单独构成排除理由。短回执可直接读，也可由 Context Mode 承载；不设固定批次数。Hook 指导、有限重写和透传不改变 owner，也不保证接管全部宿主工具。

Trellis `task.py current --json` 的 `session_source` 表示身份，`source=unbound_task|unbound_ambiguous` 表示尚未绑定任务，两者分别判断。有身份时按用户明确意图原生 `select`，再遵守任务阶段。载体无法核验身份时使用宿主原生 shell；禁止复制环境身份、借用其他会话 pointer 或制造 shell ticket。

## 当前 Trellis fork 并行工作流

本节只分流入口；Trellis Channel、子节点配置、队列和报告验收遵守当前项目已选工作流与 Trellis fork 的原生合同。先确认项目的工作流和版本，再按以下顺序路由：

1. 普通实现、审查或研究默认由主会话完成；“并行”措辞本身不构成派发授权。用户明确要求独立证据后才考虑子节点；复杂或跨组件的只读研究仍可由主会话在 `planning` 中完成。
2. 只有 `change_bearing` 工作需要原生规划封口与实施批准。研究复杂度、跨组件、依赖分析或建议本身不触发实施门；仅对会实质改变研究范围或方法的用户选择调用 `$pennix-decision-grill`。
3. 显式 subnode 工作先读项目当前 workflow 和 `trellis-channel` 的 `subnode-work` procedure 及多目标派发 reference；首次 spawn/send 前，目标 task 必须包含冻结的研究问题、unit 映射/合并理由、brief 范围与停止条件/报告落点、并行和 FIFO 接受策略，并取得用户明确批准。该批准仅授权列明的 evidence work；实质改变派发方案需重批。inline 不禁止 Channel 独立证据；缺少独立报告不能静默降级成主代理通过结论。本 Skill 不复制 schema、FIFO 或 validator。
4. 多个独立 evidence units 只有在项目可靠性门满足后才进入 FIFO queue。读取项目 `.trellis/agents/subnode-profiles.json`，由 Trellis profile 动态解析模型与 reasoning effort；Skill 不写死映射。仅在证据难度或风险足以说明时选择 `xhigh`。
5. 创建/派发、发送、barrier/wait、队列推进均走 `$trellis-channel` 与当前 fork 的原生 Channel 命令。使用一个原生终态 wait；不得用持续轮询、多个 waiter、自动重试或常驻调度器代替通知/等待合同。
6. Worker 终态只表示执行结束，不等于结果验收。协调者核验报告完整性、引用来源和受保护目标，再写入一次 disposition 后才能推进下一项。
7. Trellis 任务、Channel、profile、queue、`spawn/send`、`barrier/wait` 和状态转换实际调用 Trellis 原生接口。普通 CLI 仅在 integration 条件满足时使用执行载体；宿主 continuation 保留原生入口，不改成后台 job 或代理轮询。
8. 临时任务切换用原生 `task.py select` 绑定规划上下文，不能以 start 代替选择或批准。有在途节点时按 Channel procedure 暂停补位、排空所有已派节点与 reservation、保存未派队列和原阶段后再 select；不自动重启用户已停止的任务。普通继续/压缩恢复保持断点快路径。

## 本地证据优先

- 涉及当前机器、当前项目、工作树、源码、配置、日志或已存在资源时，本地检索和派生默认使用 Context Mode，并可结合已批准的 CodeGraph；本地证据已足以回答时，不启动 `$pennix-grok-search`、`$pennix-tavily-search` 或 `$pennix-windsurf-code-search`。
- 本地存在目标源码但问题要求当前上游状态、公开资料、跨项目比较或外部事实时，才进入外部检索；外部检索结果仅补充或对照本地证据，不能替代本地事实核验。
- 本地检索结果为空、过时、无法解释，或用户明确要求外部来源时，按上表进入对应外部路径；用户明确指定的来源优先于本默认顺序，但仍不改变任务和凭据边界。
- `$pennix-grok-search` 的可发现性不构成自动调用理由；调用前必须先判断问题是否确实需要外部资料。

## 外部检索降级

- 普通外部检索必须先走 `$pennix-grok-search`，搜索显式使用 `--no-extra`；`--extra N` 仅在当前请求明确要求或已经获得批准时使用。CLI 自有的有界尝试不构成代理重试；代理不重复整个命令。正确构造的单次 Grok
  操作若因上游/网络错误、配额、超时、不可用前置条件、来源导致的命令失败或
  畸形响应而不可用，才将同一个有界请求交给自托管 `$pennix-tavily-search` 一次。
- 不支持的 CLI 选项、缺少必需参数等可在本地改正的调用/用法错误，先改正调用，不能直接触发降级。
- 降级只用于有界搜索和已知页面读取；原请求为 map、crawl 或 research 时，只能收敛为满足请求所需的
  搜索加页面读取，不宣称具备原路径的等价语义。
- Grok 已返回满足当前请求的可用降级结果时直接消费，不触发 Hikari；只有整个命令不可用才允许这一次降级。代理不重试、不并行双跑、不改配置、不读取配置判断 provider、不暴露诊断中的敏感信息、不再选择第三个 provider。
  保留用户、task 或 system 指定的来源、工具、时效、隐私和范围约束，并在对外结果中简要说明路由发生变化。
- 若自托管 Tavily 路径也不可用，报告检索缺口并停止；显式要求特定工具或来源的更高优先级指令始终覆盖本默认规则。

## 组件职责

SiYuan 的 `web_search`、`web_fetch` 和 `http_request` 只服务实际知识操作，如用户要求的来源导入。独立网页调研、Codex 官方资料和本地项目定位仍走各自入口，不能借用思源工具作为通用检索或其他检索工具的降级路径。保留思源原生能力，按调用意图选择。

知识、历史回溯和规则晋升按用户意图选择唯一主要来源，见
[`references/knowledge-promotion.md`](references/knowledge-promotion.md)。已配置思源的人工知识操作由
`pennix-siyuan-knowledge` 使用原生 MCP；当前 task/源码/spec、`trellis mem` 历史和 formal handoff
各保留自身状态和规定接口。中文技术知识的撰写或改写加载 `$pennix-chinese-tech-writing`，保存仍需具体用户授权。知识失败不阻断任务或交接，禁止无条件预加载、自动捕获与双向同步。

- `Trellis` 是项目 task、任务文件、跨会话状态和工作节点生命周期的权威；context-mode 不决定项目任务语义。正式 handoff 的 `source.rollout.session_id` 只是来源 provenance；目标绑定只能来自当前 Trellis 直接解析的 `source=session:<target-key>`，不能把旧 session 或 `session-fallback:<key>` 当作目标。
- 项目 `AGENTS.md` 与 `.trellis/spec/` 保存项目事实、任务合同和项目特殊路由；Skill 不覆盖更近的项目规则。Trellis 原生模板、骨架与机械惯例优先，自定义中文正文采用写作方法；生成资产仍回实际模板来源修改。
- CodeGraph 配置、使用边界和原生 MCP/CLI 手册索引交 `$pennix-codegraph-integration`；系统部署交 lifecycle，项目操作保留其原生入口与明确授权。
- 确有独立证据价值的工作遵循当前项目选择的 Trellis `subnode` procedure。Trellis 维护其 brief、持久化报告和
  Channel 生命周期；主会话保留项目事实、验收和 Git，不把该合同复制为用户级 Skill。
- 已初始化 Trellis 项目的 bundled `trellis-research-record` 将核验后的研究事实、候选、不确定项和下一动作写入当前 task；它不是第二套事实台账。
- 已初始化项目的 Trellis 资产更新和已选 workflow 刷新由 `$pennix-trellis-project-update` 负责，必须调用当前 Trellis fork 的原生 `trellis update` / `trellis workflow`；系统级组件部署仍由 `$pennix-component-lifecycle` 负责，`$pennix-trellis-asset-check` 只做只读诊断。
- `pennix-session-handoff` 只处理用户明确要求的正式交接；其 immutable core、append-only lifecycle receipt 和确定性 retention 归它所有，但不拥有 Trellis task/pointer。对带 task 的新协议，Skill 只编排 Trellis 原生 `ownership quiesce|seal|retire|claim|consume|archive`，不得自行写 pointer；正式交接通过本地来源封口和配对包验证记录来源收敛。初始 admission 只在 core、prompt、`$trellis-start` 和当前事实完整核对后记录一次 `reconciled`，不完整消费不写 target reservation；后续 `claim` 必须有新的明确继续授权。
- 系统组件部署和 Skills 物化由 `$pennix-component-lifecycle` 编排已登记动作；CodeGraph 项目操作归其原生入口，Hook 实现和配置归事件所属组件及宿主的原生入口。普通路由请求不授权这些高影响动作。
- 工作流资源清理由 `$pennix-resource-cleanup` 负责流程路由；Trellis、Grok、context-mode、服务、容器、系统和远程主机仍分别拥有自己的资源与清理合同。路由 Skill 不执行全局回收，也不替 owner 删除目录。
- Hook/config 和拥有该行为的运行时负责必须发生的事件、阻断、信任、生命周期和审计；提示词只能表达决策原则，不能宣称确定性保证。

## 禁止混淆

- Context Mode 的索引、摘要和恢复材料不自动成为 task、Issue、授权或配置事实；关键结论回到当前权威来源核验。
- 不用执行器重实现 Trellis channel watcher、事件等待、Hook 交互或其他已有专用协议；不通过轮询替代生命周期等待。
- `$pennix-grok-search` 负责外部检索，载体不接管其网络调用、凭据读取、备用供应商或错误协议。
- `openai-docs` 负责其允许的 OpenAI/Codex/API/ChatGPT 官方资料路径；它与 Grok 优先的外部检索各自遵守规定接口。
- 不因“用户希望并行”就自动派发 worker；没有独立证据价值时保留主会话 inline 路径。
- 不将凭据、会话、缓存、数据库、日志、运行态、原始外部响应或未经核验的候选提交到 Git；Context Mode 本地索引按集成 Skill、用户指令和来源 owner 合同处理，可保存带来源及未核验状态的候选。

## 输出

路由结论应简要说明：请求语义、唯一责任组件、是否需要先读项目规则、候选如何核验、是否允许持久化、所需用户授权和
停止条件。若基础工具按正确原生调用仍不可用，保留原错误并停止；外部网络检索仅可按“外部检索降级”使用一次
自托管 Tavily 路径，其他路径不要用第二套状态机、替代 provider 或自定义重试掩盖能力缺口。
