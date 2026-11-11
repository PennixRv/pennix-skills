# 收敛 Context Mode 路由 Skill 合同

## 目标（Goal）

根据根任务 10-20-context-mode-routing-alignment 的已批准完整方案，更新 Context Mode 集成与跨组件路由 Skill，并按 Windsurf 来源提交固定集合来源。

## 需求（Requirements）

- 更新 `skills/pennix-context-mode-integration/SKILL.md`，采用默认 Context Mode 与有限负面清单；分别区分命令执行、内容处理和持久本地索引，不按组件、路径或敏感标签设普遍禁用规则。
- 只把宿主专有接口，以及当前调用确实无法保留必要运行语义的情形列为原生入口例外；要求以实际工具/源码/回执为依据，不以工具发现错误或一次调用失败推断不可用。
- 允许保留带来源及“未核验”状态的 Windsurf 候选；在作为事实使用前回到当前源码核验。短回执可原生直达，也可用 Context Mode。
- 更新 `skills/pennix-workflow-routing/SKILL.md`，仅同步职责与入口规则，引用集成 Skill 作为唯一详细政策来源；不将 Git 状态写入或候选来源合并为通用禁令。
- 在 `collection.json` 中按实际 Windsurf 源提交固定集合来源；集合成员必须由既有原生物化流程生成，不直接编辑已生成成员。
- 保留实际 Skill 名称、职责、组件授权、宿主接口、工具来源和全文读取合同；不得改动 Hook、其他集合成员或生命周期状态机。

## 约束（Constraints）

- 所有源改动在本仓库现有 `main` 上完成；不创建分支。
- Windsurf 来源更新依赖 `windsurf-code-search` owner 提交；本任务只更新集合清单和生成物，不复制组件源码。
- 根任务 `.trellis/tasks/10-20-context-mode-routing-alignment` 保存跨组件方案与最终验收；本任务只记录 `pennix-skills` 的源、检查、固定提交和集合物化证据。

## 验收标准（Acceptance Criteria）

- [ ] 集成 Skill 具备默认规则与两类有证据边界的原生入口例外，分别处理执行、内容分析和持久索引。
- [ ] 路由 Skill 与集成 Skill 一致，职责和唯一细节来源清楚；不再保留宽泛的组件、项目外路径、状态写入或未核验候选禁令。
- [ ] `collection.json` 指向实际已验收的 Windsurf 源提交；集合检查、引用/元数据检查和适用测试通过，生成成员与源一致。
- [ ] 本仓库只在 `main` 提交并推送至真实 `origin/main`；最终提交 SHA、集合来源和检查结果记入本任务及根任务。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
