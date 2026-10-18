# 澄清 Context Mode 工具面证据与组件原生调用边界

## 目标（Goal）

按已批准的根任务方案，精简修正 Context Mode 集成与跨组件路由两项 Skill，区分宿主 MCP、functions 内嵌工具、Context Mode tools/list 与 Hook 命中证据，并明确组件原始调用走 owner 原生入口、结果按需交给 Context Mode 分析。

## 需求（Requirements）

- 只修改 `skills/pennix-context-mode-integration/SKILL.md` 和 `skills/pennix-workflow-routing/SKILL.md`；不修改用户级 `AGENTS.md`、组件源码、生命周期状态或安装资产。
- 明确区分宿主外层 MCP 工具面、`functions` 内嵌工具面、Context Mode `tools/list` 与 `PreToolUse` matcher/decision 四层证据；任一层缺失或失败不得推断其他层缺失。
- 明确组件原始调用仍由 owner 原生入口负责；Context Mode 只作为符合 owner 合约的本地非交互执行载体，或对已取得的回执做筛选、聚合和摘要。
- 保留宿主交互、Channel continuation、原生 MCP、生命周期/Trellis/CodeGraph 协议、部署发布、凭据和长任务的原生边界，避免扩大 Skill 适用范围。

## 验收标准（Acceptance Criteria）

- [ ] 两个 Skill 的边界文字与上述需求一致，且没有把 `functions` 嵌套入口误写成宿主外层工具面。
- [ ] 组件 owner、允许载体、状态写入者和原生协议边界仍可从路由表判断。
- [ ] `scripts/quick_validate.py` 分别通过两个 Skill；`tests/test_collection.py` 通过。
- [ ] `git diff --check` 通过，任务记录、组件提交和远端引用可追溯。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
