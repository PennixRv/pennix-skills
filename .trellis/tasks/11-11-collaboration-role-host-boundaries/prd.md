# 协作角色与宿主工具边界修订

## 目标（Goal）

关联根任务 collaboration-tool-capability-audit 第11版已批准合同 WP2：修正角色优先、宿主工具条件、共享集合路径和协作命名，不增加Skills数量或交互协议。

## 需求（Requirements）

- 执行根任务 collaboration-tool-capability-audit 第 11 版合同 WP2；用户批准及跨组件验收由根控制任务保存，不另授予交互或部署权限。
- 工作流总路由与决策方法先判断主 Agent、Trellis 团队成员、Paseo 委派 Agent 的职责，再适配当前宿主工具。
- 修正资产检查与正式交接的共享集合路径示例，保留 PENNIX_SKILLS_ROOT 覆盖及 Codex state schema 5 边界。
- 不增加成员，不改变 collection.json 的来源、许可或物化规则。

## 验收标准（Acceptance Criteria）

- [x] 角色边界、机制/执行者命名及宿主条件已写入相关正文。
- [x] `python3 scripts/collection.py verify` 通过，维持 19 Skills、2 commands。
- [ ] 差异与中文文案核对通过；正式宿主发现和调用由根控制任务集成验收。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
