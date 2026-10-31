# 实施计划：Pennix Skills 主线路由与正式会话交接适配

## 执行前条件

- 父任务 revision 5 方案已获用户批准并由根仓原生 CLI 启动；本 Pennix Skills owner task 完成本轮方案收敛并经本仓原生 `seal/approve/start` 后，才可修改源码。
- 核验本 worktree 的 HEAD 为 `088caf16cfd6ff4e20fe08adbb1d503f9d715642`、目标分支为 `main`，并确认无未识别差异。
- 主线路由可在 Trellis owner task 步骤 2–3 的任务合同、阶段 workflow 与 resolver 形成后准备；引用查询、错误码或 revision 的细节在根侧组合验收前对照步骤 4 的冻结合同。正式会话交接 adapter 只在步骤 4 冻结 CR/ownership 接口后实施，未完成时只暂停该附加工作包，不阻断主线路由。

## 有序步骤

1. **更新主线路由。** 审计并修改 `skills/pennix-workflow-routing/SKILL.md` 及必要的 `references/knowledge-promotion.md`，统一五个阶段、Trellis Teamwork、Paseo/Lifecycle、检索、代码定位、Context Mode、宿主原生入口和状态写入边界。明确 owner、source repository、安装工具、state writer、allowed transport、exit conditions 和 replan trigger；保留按需参与、跳过和回流的灵活性。
2. **同步决策协助。** 更新 `skills/pennix-decision-grill/SKILL.md` 与其 contract test，使阶段 2 的决策树、阶段 3 的方案收敛、外部开源参考和实施中新取舍的处理边界一致。明确用户批准、Trellis 规划入口和 Skill 建议之间的关系，不复制阶段状态或增加固定审批。
3. **验收主线路由。** 运行 routing、decision-grill 的现有测试和 collection 校验；检查 Skill 首屏、reference 相对链接、术语和五阶段参与描述。形成不含 session-handoff adapter 的主线提交，并记录该提交和可供父任务步骤 8 固定的验收收据。
4. **实现正式会话交接 package adapter。** 在 Trellis 接口冻结后，按 `pennix-session-handoff` 当前脚本与 Skill 合同调整 adapter：保留 `validate`、ready、core 分页、prompt 配对、历史按需读取、Trellis start、事实核对和 ownership generation 条件；明确任务阶段与正式会话交接分离；拒绝未经授权的 claim/consume/archive 和任何 pending next action。只更新该 package 的脚本、Skill、测试及必要的 OpenAI 元数据。
5. **验收附加 package 并收束 owner task。** 运行 handoff 的现有单元和流式测试，覆盖不完整接纳、分页缺口、ready 收据、身份/代数、归属屏障、prompt 渲染和停止边界；运行全量相关 Python 测试、collection 校验与 `git diff --check`。主线路由保留步骤 3 的提交，附加适配形成后续独立提交；分别记录两类结果、风险、提交和根侧接纳引用，之后完成 Pennix Skills owner task。

步骤依赖：1 → 2 → 3；步骤 4 只依赖 Trellis owner task 步骤 4，不依赖步骤 1–3；步骤 5 在步骤 3、4 各自通过后执行。步骤 4 失败或未完成不回退主线路由，主线收据仍可供根侧验收；附加 package 未完成时不宣告父任务全部交付完成。

## 验证命令

以仓库现有入口为准执行并记录：

```bash
python3 -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'
python3 -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'
python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py'
python3 -B scripts/collection.py verify
git diff --check
```

collection 验证按 `verify` 子命令执行；不新增验证工具。

## 唯一停止点

主线路由和 formal session handoff package 均完成各自测试、collection 校验、差异审查并记录提交和收据后，停止本 owner task，等待根任务分别接纳主线和附加 package。此处不修改根仓 gitlink，不发布、不安装、不执行正式交接运行时操作。

## 回退

每个 work package 在本 owner task 的独立提交中保留可回退边界。路由文本或 contract test 失败时在步骤 1–3 内修复；adapter 的 ready、身份、generation 或 Trellis 接口不一致时停止步骤 4，不以兼容旁路掩盖合同差异。只有未接纳的局部提交需要撤回时才回退该提交，不重写目标分支历史，也不删除用户运行态或交接收据。

<!-- trellis-implementation-plan:v1 -->
```json
{
  "schema_version": 1,
  "steps": [
    {
      "id": "skills-mainline-routing",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills",
        "base_commit": "088caf16cfd6ff4e20fe08adbb1d503f9d715642",
        "component_or_path": "skills/pennix-workflow-routing/SKILL.md; skills/pennix-workflow-routing/references/knowledge-promotion.md; routing tests"
      },
      "depends_on": [],
      "action": "基于 Trellis owner task 步骤 2–3 形成的任务合同、阶段 workflow 与 resolver，审计并更新现有 pennix-workflow-routing，准确表达五阶段职责、Trellis Teamwork、按需组件路由、Paseo/Lifecycle 边界、外部参考与 Trellis CLI 状态写入边界；保留跳过、回流和条件依赖，不增加独立 Paseo Skill。",
      "deliverables": "主线路由 Skill 与必要 reference 的最小差异；owner、源码仓库、安装工具、state writer、allowed transport、退出条件和重新规划触发条件的准确说明；相关合同测试更新。",
      "verification": "运行 `python3 -B scripts/collection.py verify` 和 `python3 -B -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'`；检查 Skill 首屏、相对链接、术语及路由按需性。",
      "risks": "若路由文字与 Trellis 当前稳定合同不一致，会产生错误调用；若把所有组件列为必需，会过度限制阶段路由。",
      "rollback": "只回退本步骤中未通过验收的 routing Skill、reference 和对应测试改动，不修改其他工作包或用户安装资产。"
    },
    {
      "id": "skills-decision-grill",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills",
        "base_commit": "088caf16cfd6ff4e20fe08adbb1d503f9d715642",
        "component_or_path": "skills/pennix-decision-grill/SKILL.md; skills/pennix-decision-grill/tests/test_contract.py"
      },
      "depends_on": ["skills-mainline-routing"],
      "action": "核对并更新 decision-grill 与阶段 2 决策空间、阶段 3 方案收敛、外部参考和实施中实质新取舍的协作合同；保留同步用户决策，不重复询问事实或已定选择，不替代 Trellis 规划、状态写入或用户批准。",
      "deliverables": "与父任务及 routing Skill 对齐的 decision-grill 合同；覆盖职责边界和按需提问的合同测试。",
      "verification": "运行 `python3 -B -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'`；检查决策提问仍使用原生同步交互，且未引入状态转换或强制审批。",
      "risks": "提问规则若重复已知事实会增加交互负担；若把建议误写成批准会越过用户决策边界。",
      "rollback": "只回退未通过验收的 decision-grill 文本与测试改动，保留 routing 工作包已接受的结果。"
    },
    {
      "id": "skills-mainline-acceptance",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills",
        "base_commit": "088caf16cfd6ff4e20fe08adbb1d503f9d715642",
        "component_or_path": "routing/decision-grill tests; scripts/collection.py; mainline acceptance receipt"
      },
      "depends_on": ["skills-decision-grill"],
      "action": "独立验收 Pennix Skills 主线路由与同步 Grill，核对 collection、相关测试、链接、职责边界及需由父任务复核的集成证据；形成不含 session-handoff adapter 的主线提交，并记录本工作包提交和收据。",
      "deliverables": "主线路由 work package 验收收据、主线专属源码提交引用、测试与 collection 结果及未解决风险；供父任务步骤 8 独立固定。",
      "verification": "运行 routing 与 decision-grill 合同测试、`python3 -B scripts/collection.py verify` 和 `git diff --check`；根侧集成测试由父任务按步骤 8 执行。",
      "risks": "组件内通过不能证明与目标 Trellis CLI 或 Paseo 版本集成正确；根侧验收仍须消费对应组件证据。",
      "rollback": "主线验收失败时保留差异和失败证据，不提供主线通过收据，不影响独立附加适配的验证。"
    },
    {
      "id": "session-handoff-package-adapter",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills",
        "base_commit": "088caf16cfd6ff4e20fe08adbb1d503f9d715642",
        "component_or_path": "skills/pennix-session-handoff/SKILL.md; scripts/workflow_contracts.py; scripts/handoff.py; scripts/render_handoff_prompt.py; tests/"
      },
      "depends_on": [],
      "action": "在 Trellis 原生验证步骤冻结 CR/ownership 查询与受控操作接口后，按 pennix-session-handoff 当前合同实现独立 adapter；保留 ready 收据、core 分页、prompt 配对、history 按需读取、Trellis start 和事实核验；不得推进任务阶段或执行 pending next action。",
      "deliverables": "formal session handoff package adapter、相关测试与独立验收收据；与主线路由及任务阶段分离的明确边界。",
      "verification": "运行 `python3 -B skills/pennix-session-handoff/tests/test_handoff.py`、`python3 -B skills/pennix-session-handoff/tests/test_render_handoff_prompt.py` 和 `python3 -B skills/pennix-session-handoff/tests/test_streaming_handoff.py`，覆盖 ready、core 分页、prompt 配对、history 按需读取、任务归属授权和停止边界；运行 `python3 -B scripts/collection.py verify` 与 `git diff --check`。",
      "risks": "Trellis 接口未冻结会导致适配漂移；ready 或 ownership 状态若被误当作阶段或执行授权，会改变既定安全边界。",
      "rollback": "接口不一致或验收失败时停止附加工作包并回退其未接纳差异，不改变主线路由收据、主线验收或运行态。"
    },
    {
      "id": "session-handoff-acceptance-and-closeout",
      "target": {
        "repository": "pennix-skills",
        "branch": "pennix/new-fork-workflow-skills",
        "base_commit": "088caf16cfd6ff4e20fe08adbb1d503f9d715642",
        "component_or_path": "skills/pennix-session-handoff/tests/; collection.json; final owner task acceptance receipt"
      },
      "depends_on": ["skills-mainline-acceptance", "session-handoff-package-adapter"],
      "action": "分别核验主线路由和附加 package 的测试、collection、差异与提交收据，确保主线提交与后续附加适配提交各自可追溯，记录各自验收状态并完成 Pennix Skills owner task；不更新根仓 gitlink、不发布或安装。",
      "deliverables": "分别可追溯的主线与附加适配验收收据、主线提交及包含附加适配的后续提交引用与风险记录；根任务步骤 10 可据此更新 gitlink。",
      "verification": "运行上述三个 handoff 测试、`python3 -B -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'`、`python3 -B -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'`、`python3 -B scripts/collection.py verify` 和 `git diff --check`；确认每项收据引用当前提交，且附加 package 结果不改变主线状态。",
      "risks": "若两个 work package 的提交或收据混为一体，根任务无法按既定优先级独立接纳。",
      "rollback": "不通过时仅阻止对应 work package 接纳；保留已通过的另一 work package 证据，不改写历史或其他工作树。"
    }
  ],
  "stop_point": {
    "condition": "主线路由与正式会话交接 package 均完成各自合同测试、collection 验证和差异审查，并留下对应提交与独立验收收据；此后由根任务分别接纳主线结果及附加结果。",
    "observable_evidence": "主线路由和 decision-grill 验收、handoff adapter 验收、collection 结果、测试结果、各自提交标识与未解决风险均有独立记录；主线路由不依赖 handoff package，handoff package 不改变 Trellis 任务状态、阶段或 pending action。",
    "remaining_work": "不再有 Pennix Skills 源码或本地验收步骤；根仓 gitlink、跨组件组合验收、发布安装和现场验证仍由父任务执行。"
  }
}
```
