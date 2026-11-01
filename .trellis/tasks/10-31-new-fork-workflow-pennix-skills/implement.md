# 实施计划：Pennix Skills 审查、主线路由与正式会话交接适配

## 执行前条件

- 父任务 revision 7 方案已获用户批准并由根仓原生 CLI 启动；本 Pennix Skills owner task 完成本轮方案收敛并经本仓原生 `seal/approve/start` 后，才可开始本轮 Skill 源文件修改。
- 当前 Pennix Skills 分支已有主线路由提交 `aabe97d` 和独立会话交接适配提交 `967d18c`，其后还有待审未提交差异；保留既有提交，不重写历史。正式集合审查只读当前 16 项，不把分支上已有修改视为审查通过。
- 主线路由可在 Trellis owner task 步骤 2–3 的任务合同、阶段 workflow 与 resolver 形成后准备；引用查询、错误码或 revision 的细节在根侧组合验收前对照步骤 4 的冻结合同。正式会话交接 adapter 只依赖 Trellis owner task 步骤 4 冻结的 CR/ownership 接口，可独立实施和验收，不等待 Pennix Skills 主线；只有最终组合提交需要同时具备两类已验收结果。

## 有序步骤

1. **审查正式集合。** 以父任务现有阶段参与表为索引，逐项阅读 `collection.json` 中 16 个 Skill 的入口说明和正文；根据实际关联再检查其 references、元数据或测试。核对触发、职责、阶段参与、相互链接、中文技术表达和父任务术语；记录适用、条件适用或排除结论及有证据的问题，不复制第二份全量目录。
2. **收敛主线路由与相关 Skill。** 核对现有 `pennix-workflow-routing`、`pennix-decision-grill` 及审查中发现的其他直接相关 Skill。修复真实的职责冲突、错误触发、无效链接、术语错误或无依据的限制；其中明确修复一般外部检索的 Tavily 优先路由，以及 Grok 的适用操作和明确选择触发条件，并遵守各自失败合同。不相关或正确的 Skill 保留原文。新写或实质改写的工作流正文使用简体中文技术文体，并复核术语；必要时依据官方 Skill 指南调整渐进披露和指令自由度，不统一长度或结构。
3. **验收主线路由与审查。** 对实际改动运行相应合同测试和 collection 校验；人工核对全量审查结论与现有阶段参与表。从 `aabe97d` 建立隔离主线 worktree，并仅转入经过审查确认的主线差异；无新差异时直接复用 `aabe97d`。形成不含会话交接适配的可固定主线提交，并记录父任务步骤 8 可消费的审查收据。
4. **独立完成正式会话交接 package。** 在 Trellis 接口冻结后，从既有 `967d18c` 建立独立分支，不等待主线路由验收；按 `pennix-session-handoff` 当前脚本与 Skill 合同审查已有 adapter 差异并按证据调整。保留 `validate`、ready、core 分页、prompt 配对、历史按需读取、Trellis start、事实核对和 ownership generation 条件；明确业务阶段转换与正式会话交接彼此独立；不执行未经授权的 claim/consume/archive 或 pending next action。只改该 package 确需调整的脚本、Skill、测试或元数据，并单独记录测试与验收收据。
5. **分别验收并完成最终组合。** 独立核验主线路由与会话交接 package 的测试、collection、差异和提交收据。两者通过后，从已验收主线提交建立最终延续分支，接入 `967d18c` 中的既有适配及独立验收的新适配差异，运行组合验证并记录最终提交；不改写既有提交。附加适配及其组合提交不改变主线验收或发布资格。完成 Pennix Skills owner task 后等待根任务分别接纳主线和附加适配。

步骤依赖：1 → 2 → 3；主线审查与会话交接适配各自依赖其明确的接口输入，后者只等待 Trellis owner task 步骤 4 冻结接口，不等待主线验收。步骤 5 在主线和附加适配分别通过后执行最终组合。任一工作包失败只暂停其自身及最终组合，不回退另一工作包已验收结果；附加 package 未完成时不宣告父任务全部交付完成。

## 验证命令

以仓库现有入口为准，按实际改动运行相关检查并记录：

```bash
python3 -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'
python3 -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'
python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py'
python3 -B scripts/collection.py verify
python3 skills/pennix-chinese-tech-writing/scripts/lint_copy_rules.py <本轮新增或实质改写的中文正文>
git diff --check
```

中文文案脚本用于发现需要人工判断的语言问题，不把其样式建议或无关历史文件结果设为提交门槛；未改动的 Skill 不为追求全量格式统一而改写。

collection 验证按 `verify` 子命令执行；不新增验证工具。

## 唯一停止点

16 项正式 Skill 审查完成并留有结论；主线路由和 formal session handoff package 均完成各自测试、collection 校验、差异审查并记录提交和收据；会话交接延续分支先包含可供根任务固定的主线提交，再以独立后续提交包含附加适配。满足后停止本 owner task，等待根任务分别接纳两类结果。此处不修改根仓 gitlink，不发布、不安装、不执行正式交接运行时操作。

## 回退

每个 work package 在本 owner task 的独立提交中保留可回退边界。路由文本或 contract test 失败时在步骤 1–3 内修复；adapter 的 ready、身份、generation 或 Trellis 接口不一致时停止步骤 4，不以兼容旁路掩盖合同差异。只有未接纳的局部提交需要撤回时才回退该提交，不重写目标分支历史，也不删除用户运行态或交接收据。

<!-- trellis-implementation-plan:v1 -->
```json
{
  "schema_version": 1,
  "steps": [
    {
      "id": "skills-formal-collection-review",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills",
        "base_commit": "967d18cfcd38303cbe34913632fafcfb045aa4ca",
        "component_or_path": "collection.json 中的 16 项 skills/*/SKILL.md；按具体问题查看其 references、agents/openai.yaml 和相关测试；父任务 research/pennix-skill-phase-participation-audit.md"
      },
      "depends_on": [],
      "action": "只读审查正式集合 16 项 Skill 的触发描述、职责、工作流阶段参与、相互链接和中文技术表达；按需要核验 references、元数据和测试。使用父任务现有阶段参与表作为关系索引，在本 owner task execution.md 记录覆盖范围、重要发现和结论，不复制第二份全量目录。参考 Anthropic/OpenAI 官方 Skill 作者指南及 pennix-chinese-tech-writing；按任务需要和风险校准渐进披露与指令自由度，不把指南示例变成格式或规模门槛。",
      "deliverables": "16 项正式 Skill 的完整适用性审查收据；按适用、条件适用或排除说明其与目标工作流的关系；可核验的问题与后续 owner 处置依据。",
      "verification": "确认审查对象与当前 collection.json 的 16 项一致；每项均有审查结论或明确的引用依据；与父任务现有阶段参与表对照并记录差异，不另建重复清单。",
      "risks": "只看 Skill 名称或描述会漏掉实际触发与交叉链接；把全量审查误解为全量重写会造成无价值差异。",
      "rollback": "本步骤只读，不改变源资产；若审查记录有误，修正对应记录并复核来源。"
    },
    {
      "id": "skills-mainline-routing",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills-mainline-review",
        "base_commit": "aabe97dbb8a9a7f71eebb8cb30a40506cace7c20",
        "component_or_path": "skills/pennix-workflow-routing/、skills/pennix-decision-grill/、skills/pennix-grok-search/、skills/pennix-tavily-search/，以及审查确认直接参与工作流且存在问题的其他正式集合 Skill；仅按具体问题涉及相应 references、元数据和测试"
      },
      "depends_on": ["skills-formal-collection-review"],
      "action": "在从 aabe97d 建立的隔离主线 worktree 中，依据正式集合审查结果及 Trellis owner task 步骤 2–3 的稳定任务合同、阶段 workflow 与 resolver，复核当前已修改的 workflow-routing 差异，并仅转入 pennix-workflow-routing 和其他直接相关且有证据问题的 Skill；准确表达各业务阶段职责、Teamwork、按需组件路由、Paseo/Lifecycle 边界、外部参考和 Trellis CLI 状态写入边界。按父任务决策将一般外部检索路由为优先 Tavily，仅在操作适合或用户/当前路线明确选择时使用 Grok；保留各 Skill 的失败合同和用户来源约束，不自动轮换服务商。保留跳过、回流和条件参与，不增加独立 Paseo Skill；无问题资产不改写。",
      "deliverables": "主线路由与经证据确认受影响的 Skill/reference 的最小差异或无需改动的审查结论；owner、源码维护仓库、安装工具、state writer、allowed transport、退出条件和重新规划触发条件的准确说明；与父任务一致的外部来源优先级、Grok 适用条件及失败边界；仅对变更文件更新的相关合同测试。",
      "verification": "运行 `python3 -B scripts/collection.py verify` 和所有实际受影响 Skill 的现有合同测试；检查触发、职责、相对链接、术语及按需参与，并验证一般外部检索优先 Tavily、Grok 仅按操作适用性或明确选择触发且失败处理遵循各 Skill 合同。对新增或实质改写的中文正文运行中文技术写作只读检查并人工判断结果，不把样式建议变成统一门槛。",
      "risks": "若路由文字与 Trellis 当前稳定合同不一致，会产生错误调用；若把所有组件列为必需，会过度限制阶段路由。",
      "rollback": "只回退本步骤中未通过验收的 routing Skill、reference 和对应测试改动，不修改其他工作包或用户安装资产。"
    },
    {
      "id": "skills-decision-grill",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills-mainline-review",
        "base_commit": "aabe97dbb8a9a7f71eebb8cb30a40506cace7c20",
        "component_or_path": "skills/pennix-decision-grill/SKILL.md; skills/pennix-decision-grill/tests/test_contract.py"
      },
      "depends_on": ["skills-mainline-routing"],
      "action": "在隔离主线 worktree 中核对当前 decision-grill 差异及“决策空间构造与归并”的候选/条件分支、“解决方案设计与收敛”的方案收敛、外部参考和“任务实施”中的实质新取舍协作合同；只在有条件分支时使用决策树，简单选择保留合适表达；不重复询问事实或已定选择，不替代 Trellis 规划、状态写入或用户批准。",
      "deliverables": "与父任务及 routing Skill 对齐的 decision-grill 合同；覆盖职责边界和按需提问的合同测试。",
      "verification": "运行 `python3 -B -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'`；检查决策提问仍使用原生同步交互，且未引入状态转换或强制审批。",
      "risks": "提问规则若重复已知事实会增加交互负担；若把建议误写成批准会越过用户决策边界。",
      "rollback": "只回退未通过验收的 decision-grill 文本与测试改动，保留 routing 工作包已接受的结果。"
    },
    {
      "id": "skills-mainline-acceptance",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills-mainline-review",
        "base_commit": "aabe97dbb8a9a7f71eebb8cb30a40506cace7c20",
        "component_or_path": "routing/decision-grill tests; scripts/collection.py; mainline acceptance receipt"
      },
      "depends_on": ["skills-decision-grill"],
      "action": "独立验收正式集合审查及 Pennix Skills 主线修订，核对审查收据、collection、受影响测试、链接、职责边界、中文文体、统一术语和需由父任务复核的集成证据；在隔离主线 worktree 形成不含 session-handoff adapter 的主线提交，并记录可供父任务步骤 8 固定的提交和收据。",
      "deliverables": "正式集合审查结论、主线路由 work package 验收收据、可独立固定的主线提交引用、测试与 collection 结果及未解决风险；供父任务步骤 8 接纳。",
      "verification": "运行受影响 Skill 合同测试、`python3 -B scripts/collection.py verify` 和 `git diff --check`；复核审查结论覆盖当前正式集合 16 项且没有把条件参与变成必调。根侧集成测试由父任务步骤 8 执行。",
      "risks": "组件内通过不能证明与目标 Trellis CLI 或 Paseo 版本集成正确；根侧验收仍须消费对应组件证据。",
      "rollback": "主线验收失败时保留差异和失败证据，不提供主线通过收据，不影响独立附加适配的验证。"
    },
    {
      "id": "session-handoff-package-adapter",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills-session-handoff-final",
        "base_commit": "967d18cfcd38303cbe34913632fafcfb045aa4ca",
        "component_or_path": "skills/pennix-session-handoff/SKILL.md; scripts/workflow_contracts.py; scripts/handoff.py; scripts/render_handoff_prompt.py; tests/"
      },
      "depends_on": [],
      "action": "在 Trellis 原生验证步骤冻结 CR/ownership 查询与受控操作接口后，从 967d18c 建立独立会话交接 worktree；审查现有及未提交 adapter 差异，仅按证据修订并独立运行测试，不等待 Pennix Skills 主线验收。保留 ready 收据、core 分页、prompt 配对、history 按需读取、Trellis start 和事实核验；不得推进任务阶段或执行 pending next action。",
      "deliverables": "formal session handoff package adapter 的独立验收提交和收据；与主线路由及任务阶段分离的明确边界。",
      "verification": "运行 `python3 -B skills/pennix-session-handoff/tests/test_handoff.py`、`python3 -B skills/pennix-session-handoff/tests/test_render_handoff_prompt.py` 和 `python3 -B skills/pennix-session-handoff/tests/test_streaming_handoff.py`，覆盖 ready、core 分页、prompt 配对、history 按需读取、任务归属授权和停止边界；运行 `python3 -B scripts/collection.py verify` 与 `git diff --check`。",
      "risks": "Trellis 接口未冻结会导致适配漂移；ready 或 ownership 状态若被误当作阶段或执行授权，会改变既定安全边界。",
      "rollback": "接口不一致或验收失败时停止附加工作包并回退其未接纳差异，不改变主线路由收据、主线验收或运行态。"
    },
    {
      "id": "session-handoff-acceptance-and-closeout",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills-session-handoff-final",
      "base_commit": "skills-mainline-acceptance 输出的主线提交；整合已验收 session-handoff-package-adapter",
        "component_or_path": "skills/pennix-session-handoff/tests/; collection.json; final owner task acceptance receipt"
      },
      "depends_on": ["skills-mainline-acceptance", "session-handoff-package-adapter"],
      "action": "分别核验主线路由和附加 package 的测试、collection、差异与提交收据。两类工作包独立通过后，从主线验收提交建立最终延续分支，接入既有 967d18c 适配及独立验收的新适配差异，运行组合测试并确保主线提交与附加适配提交各自可追溯。记录两类验收状态并完成 Pennix Skills owner task；不更新根仓 gitlink、不发布或安装。",
      "deliverables": "分别可追溯的主线与附加适配验收收据、主线提交、独立适配提交及包含两者的最终后续提交引用与风险记录；根任务步骤 10 可据此更新 gitlink。",
      "verification": "在最终延续分支运行上述三个 handoff 测试、`python3 -B -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'`、`python3 -B -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'`、`python3 -B scripts/collection.py verify` 和 `git diff --check`；确认每项收据引用对应提交、最终分支包含主线提交和独立附加适配，且附加 package 不改变主线验收状态。",
      "risks": "若两个 work package 的提交或收据混为一体，根任务无法按既定优先级独立接纳。",
      "rollback": "不通过时仅阻止对应 work package 接纳；保留已通过的另一 work package 证据，不改写历史或其他工作树。"
    }
  ],
  "stop_point": {
    "condition": "16 项正式 Skill 审查有完整收据；主线路由与正式会话交接 package 均完成各自合同测试、collection 验证和差异审查，并留下对应提交与独立验收收据；会话交接延续分支基于已验收主线且未改写既有提交。",
    "observable_evidence": "主线路由和 decision-grill 验收、handoff adapter 验收、collection 结果、测试结果、各自提交标识与未解决风险均有独立记录；主线路由不依赖 handoff package，handoff package 不改变 Trellis 任务状态、阶段或 pending action；父任务可先固定主线提交，再固定包含附加适配的后续提交。",
    "remaining_work": "不再有 Pennix Skills 源码或本地验收步骤；根仓 gitlink、跨组件组合验收、发布安装和现场验证仍由父任务执行。"
  }
}
```
