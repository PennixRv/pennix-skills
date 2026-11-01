# 新 fork 工作流：Pennix Skills 审查、主线路由与正式会话交接适配

## 目标

审查 Pennix Skills 正式集合中的 16 项 Skill，核实其在目标 Trellis 工作流中的适用阶段、触发、职责边界、必要链接和写作质量；只修复有证据的问题，并确保修改后的工作流内容与目标业务阶段合同、父任务术语及中文技术写作要求一致。主线路由继续由 `pennix-workflow-routing` 与 `pennix-decision-grill` 承载；`pennix-session-handoff` 适配仍是同一 owner task 内优先级较低的独立附加工作包，单独实施、单独验收，不进入业务阶段主线路由、主线准入或主线发布集合，也不阻断主线。

## 需求

- 目标基线为 Pennix Skills `088caf16cfd6ff4e20fe08adbb1d503f9d715642`，集成目标为 `main`；源码只在本仓库的专用 owner worktree 修改。既有主线提交 `aabe97d` 与会话交接提交 `967d18c` 保持不变；主线复核从 `aabe97d` 建立隔离 worktree，会话交接适配在 Trellis 接口冻结后从 `967d18c` 独立实施，最终组合阶段再接到已验收主线提交。
- 主线路由必须明确区分 `owner`、源码维护仓库、安装工具、`state_writer`、`allowed_transport`、退出条件和重新规划触发条件；不能用 Skill 文本接管 Trellis 任务、阶段、路线、授权或接受事实。
- 主线路由应按各业务阶段的实际职责选择 Trellis、Pennix Skills、Trellis Teamwork、Paseo、CodeGraph、Windsurf Code Search、网页检索、SiYuan、Context Mode、Lifecycle 和宿主原生接口；按需参与，不将所有组件硬编码为每个阶段必需。
- 当前任务确需外部检索时优先使用 Tavily；仅在具体操作适合 Grok 或用户/当前路线明确选择 Grok 时使用 Grok。遵守所选 Skill 的失败合同和用户指定来源，不因失败自动轮换服务商。
- `pennix-decision-grill` 只处理实质用户取舍和渐进决策问题；不重复询问可查事实、已定选择或局部实现细节，不复制 Trellis 阶段状态转移，不把建议写成强制门槛。
- 复用父任务现有阶段参与审查，对正式集合 16 项 Skill 的 `SKILL.md` 逐项核对其与本工作流的关系；按需查看相关 reference、元数据和合同测试。每项给出适用、条件适用或排除结论及简短依据，不因纳入审查而默认修改。
- 对与工作流直接相关且存在证据问题的 Skill，按其原 owner 边界修改触发说明、步骤、职责、互链或术语；不相关或已经正确的内容保留原文。根仓 `pennix-skills-extra` 由父任务另行只读审查，不纳入本组件的写入范围。
- 新增或实质改写的工作流 Skill 正文及 reference 使用简体中文技术文体，并满足父任务既定术语合同；Skill 标识、frontmatter 字段、命令、API、路径和正式产品名保持准确原文。
- 参考 Anthropic 与 OpenAI 官方 Skill 撰写指南及 `pennix-chinese-tech-writing`；按实际用途采用渐进披露，依风险决定指令强度，不设统一长度、章节模板、必需 reference 数量或逐阶段必调清单。
- 路由说明必须保留各业务阶段各自的工作目标和交互边界，支持按任务跳过、回流、阻断和并行准备；阶段之间称为阶段转换，不称为 session handoff。
- 主线路由必须说明外部流行开源项目和官方来源在正式方案形成前的参考价值；参考用于校准候选、范围和风险，不替代用户决定，也不自动成为硬限制。
- `pennix-session-handoff` adapter 只在用户明确请求正式交接时运行，继续以 immutable core、prompt、history、lifecycle receipt 和 Trellis 原生任务事实为边界；不得把 `formal session handoff package`、任务阶段、任务生命周期或 next action 绑定成同一状态。
- adapter 必须消费目标 Trellis fork 的稳定查询与 ownership 接口，保留源组件与状态写入组件的区分；不得创建第二套任务状态、第二个阶段状态源、持久 handoff 台账或复制工作流事实。
- 不复制官方 Paseo Skill、Trellis runtime、Lifecycle 执行器、项目任务事实、凭据、缓存或安装副本；不修改 Trellis、Pennix Lifecycle、Paseo 或用户运行态。

## 验收标准

- [ ] `pennix-workflow-routing` 的路由判定顺序、组件职责、Trellis fork 适配和输出合同与目标业务阶段模型及单一 Trellis 状态源一致；不存在把所有组件或阶段硬编码为必需的过度限制。
- [ ] `pennix-decision-grill` 能在“决策空间构造与归并”“解决方案设计与收敛”及“任务实施”中出现实质新取舍时提供渐进提问，并明确其不写入 Trellis 状态、不代替用户批准、不代替方案规划入口。
- [ ] 两个主线路由 Skill 的测试和 collection 合同通过，所有相对链接和术语一致，未引入新的重复 Skill 或 reference。
- [ ] 正式集合 16 项均已完成适用性审查，结论与父任务阶段参与记录可相互追溯；工作流相关修改有证据和 owner 依据，干净项无无意义改写。
- [ ] 对新增或实质改写的中文工作流内容完成中文技术写作和术语复核；不存在无依据的硬限制、统一化改写或防御式重复。
- [ ] `pennix-session-handoff` adapter 在明确请求、ready 收据、核心视图与 prompt 完整阅读、Trellis 已启动和事实核对条件下能提供导航；拒绝不完整接纳、过期事实或未经授权的任务归属操作。
- [ ] adapter 测试覆盖核心分页、prompt 配对、ready 生命周期、历史按需读取、任务归属屏障和“不执行 pending next action”；该 adapter 不进入主线路由和主线发布准入。
- [ ] 主线与附加适配的独立验收收据分别引用各自提交；根任务可先固定主线提交，再在步骤 10 固定以该主线提交为基础、包含附加适配的后续提交。
- [ ] collection 验证、相关 Python 测试和 `git diff --check` 通过；记录主线和 adapter 各自的验证结果、提交、风险和回退点。

## 约束与完成边界

- 本任务覆盖父任务步骤 5 和 9。主线路由可在 Trellis owner task 步骤 2–3 的任务合同、阶段 workflow 与 resolver 形成后准备；引用查询、错误码、revision 或 ownership 接口的细节须在根侧组合验收前对照步骤 4 的冻结合同。步骤 9 的正式会话交接适配只依赖步骤 4，不等待步骤 5，也不阻断步骤 5、根侧主线发布或现场验收。
- 源码修改须等待本 owner task 完成方案审查并经原生 `seal/approve/start` 后开始；本任务不执行 package 运行时操作。
- 本 owner task 完成时只提供已验收 Pennix Skills 提交及两类 work package 收据，不固定根仓 gitlink，不发布或安装组件。

<!-- trellis-decisions:v1 -->
```json
{
  "schema_version": 1,
  "decisions": [
    {
      "id": "trellis-state-write-owner",
      "status": "decided",
      "question": "Pennix Skills 的主线路由与决策协助是否可直接维护 Trellis 任务、阶段、路线、授权或接受状态？",
      "evidence": ["codex-workflow-optimization/.trellis/tasks/10-29-new-fork-workflow-master-plan-v2/core-model.md#2-任务层级与组件权威", "codex-workflow-optimization/.trellis/tasks/10-29-new-fork-workflow-master-plan-v2/prd.md（decision: cross-component-parent-implementation-scope）"],
      "answer_or_reason": "不可以。Trellis CLI 是这些业务事实的唯一写入入口；Pennix Skills 只负责按职责路由、提供操作指导和取得用户决定，不复制或推进 Trellis 状态。",
      "impact": "确定本 owner task 两个主线路由 Skill 与 Trellis 状态写入接口的边界。",
      "reopen_when": "父任务明确改变 Trellis 状态所有权或新增经批准的写入接口。"
    },
    {
      "id": "session-handoff-package-independence",
      "status": "decided",
      "question": "正式会话交接适配与 Pennix Skills 主线路由如何安排依赖、优先级和验收？",
      "evidence": ["codex-workflow-optimization/.trellis/tasks/10-29-new-fork-workflow-master-plan-v2/prd.md（requirement: 主线与 formal session handoff package 适配分开；decision: continuity-and-handoff-owner）", "codex-workflow-optimization/.trellis/tasks/10-29-new-fork-workflow-master-plan-v2/implement.md#推进单元与执行顺序"],
      "answer_or_reason": "`pennix-session-handoff` 是本任务内优先级较低的独立附加 work package，只依赖 Trellis owner task 冻结的 CR/ownership 接口；它不属于主线路由、准入、发布或主线验收。两类 work package 分别实施和验收，附加适配失败不阻断主线，但父任务整体关闭前仍须完成其独立验收。",
      "impact": "确定本 owner task 的两个 work package 边界、步骤依赖及主线与整体收尾的关系。",
      "reopen_when": "用户改变附加适配范围，或 Trellis 稳定接口证明当前独立依赖关系无法成立。"
    },
    {
      "id": "paseo-skill-placement",
      "status": "decided",
      "question": "Pennix Skills 是否新增独立 Paseo 集成 Skill，还是由现有路由 Skill 承载 Pennix 与 Paseo 的跨组件边界？",
      "evidence": ["codex-workflow-optimization/.trellis/tasks/10-29-new-fork-workflow-master-plan-v2/external-requirements.md#4-pennix-skills-owner-task", "codex-workflow-optimization/.trellis/tasks/10-29-new-fork-workflow-master-plan-v2/prd.md（decision: pennix-paseo-skill-boundary-name）"],
      "answer_or_reason": "沿用现有 `pennix-workflow-routing` 承载跨组件路由和必要的 Paseo 操作说明；复用 Paseo 官方 Skills，不复制其 workspace/agent 操作手册，也不新增独立 Paseo 集成 Skill。",
      "impact": "限制本任务在现有 Skills 和 reference 范围内完成主线路由适配，避免形成重复的路由或 Paseo 操作合同。",
      "reopen_when": "验收证据证明现有路由合同无法承载一个职责清晰且独立必要的接口，并由父任务重新批准范围。"
    }
  ]
}
```
