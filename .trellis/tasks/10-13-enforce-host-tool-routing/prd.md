# 明确禁止混淆宿主与嵌套工具清单

## 目标（Goal）

实现根协调任务 10-13-unify-trellis-template-writing 的 Pennix Skills 源仓库部分：调整唯一权威用户级 AGENTS 模板中现有的工具可用性规则，明确禁止将 functions.exec 的 ALL_TOOLS 当作宿主直接工具清单，并要求宿主已声明所需工具时通过原生入口调用；同步调整既有模板合同测试并更新模板 revision。等待根任务方案批准后再启动。

## 要求（Requirements）

- 调整 `skills/pennix-component-lifecycle/templates/AGENTS.md.install` 职责/入口段现有工具可用性规则，将其收敛为：不得将 `functions.exec` 的 `ALL_TOOLS` 当作宿主直接工具清单；宿主已声明所需工具时，必须通过其原生入口调用。
- 保留现有“以宿主实际声明和真实回执判断可用性”“调用失败不等于工具缺失”以及调用面、服务、权限、传输和命令错误的证据边界，不重复扩写 Grill 或 routing Skill。
- 在 `skills/pennix-workflow-routing/tests/test_contract.py` 的既有权威模板合同测试中锁定禁令和强制原生调用动作；更新唯一用户模板的 SHA-256 revision。
- 待 Pennix Trellis beta 发布后，在 `skills/pennix-component-lifecycle/references/component-versions.json` 将 `trellis-cli.approved_version` 更新为实际可安装的精确版本，并由 lifecycle 测试核验 catalog 合同。
- 通过中文写作 Skill 的现有只读文案检查和 lifecycle/routing 测试；不新增英语语法检查器，不手改 `~/.codex/AGENTS.md`，不宣称静态合同证明宿主模型行为。

## 验收标准（Acceptance Criteria）

- [ ] 唯一用户模板包含精确禁令和原生入口要求，且现有错误分类与宿主声明边界保留。
- [ ] routing 合同测试覆盖新规则；lifecycle catalog 的模板 revision 与 Trellis approved version 均精确匹配实际来源。
- [ ] routing、lifecycle 和中文写作 Skill 现有测试/检查通过；未运行或无法覆盖的宿主行为明确记录。
- [ ] 源仓库提交、推送、暂存替换、`codex-agents` 原生 upgrade、discover/verify 和最终物化摘要均有回执；不手工覆盖安装副本。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
