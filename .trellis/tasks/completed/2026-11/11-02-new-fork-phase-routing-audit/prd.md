# Correct workflow phase routing boundaries

## 目标（Goal）

Remove the host planning entry from target fork phase routing and include conditional decision support in delivery review routing.

## 需求（Requirements）

- 当前宿主的 `trellis-idea-to-closed-plan` 只作为宿主任务规划与重大变更重新规划入口，不列为目标 Trellis fork 的业务阶段参与者。
- 五个阶段各自的 bundled phase Skill 保留其阶段工作职责；跨组件路由表只列按需参与的能力，不把条件性 Skill 提升为阶段门。
- 交付审查与现场收尾阶段在必要用户决定或合同要求用户接受时，路由到 `pennix-decision-grill` 协助同步交互；阶段结果仍由 Trellis CLI 核验和接受。
- 以窄范围合同测试防止上述阶段边界再次混淆。

## 验收标准（Acceptance Criteria）

- [ ] 阶段路由表不将 `trellis-idea-to-closed-plan` 列为任一目标业务阶段的参与者，并保留其规划入口职责说明。
- [ ] 交付审查与现场收尾阶段行说明 `pennix-decision-grill` 的条件性参与及其边界。
- [ ] 路由合同测试覆盖阶段名称、阶段 Skill 独立性和上述两项边界。
- [ ] `pennix-workflow-routing` 合同测试通过，工作树差异检查通过。

## 范围

只修改 `skills/pennix-workflow-routing/SKILL.md` 的业务阶段路由表及对应合同测试，不改其他 Skills、集合清单或目标 Trellis fork 资产。

## 验证

运行 `python3 -m unittest discover -s skills/pennix-workflow-routing/tests -v`，并运行 `git diff --check`。

## 回退

恢复本任务对上述两个源码文件的差异；保留任务审查记录以说明误路由根因和修复结果。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
