# Context Mode 集合与路由替代

## 目标（Goal）

落实已批准整包中的集合物化、独立 integration Skill、路由与清理合同和对应门禁。根任务 10-18-context-mode-fastctx-replacement。

## 需求（Requirements）

- 删除旧路由 Skill，新增 Context Mode integration；路由依据操作语义。
- 完整指令、精确编辑依据、宿主交互与禁止持久化内容走原生入口。
- 更新 Grok/Windsurf 固定源并原生物化；同步资源清理、lifecycle 导航及集合门禁。
- 不复制组件执行器或版本表；安装副本在根任务最终切换阶段更新。

## 验收标准（Acceptance Criteria）

- [ ] collection verify、必要合同测试和根组合门禁通过。
- [ ] 活动集合不含 FastCtx 入口或历史兼容别名。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
