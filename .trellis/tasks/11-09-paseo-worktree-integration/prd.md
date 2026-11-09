# Paseo 工作树集成的 CodeGraph 与路由合同

## 目标（Goal）

承接已批准 W3，按已验证 CodeGraph bound 接口更新能力条件、原生手册及组件路由；当前主会话实施与验收。

## 需求（Requirements）

- 将绝对禁止 linked worktree 的旧约束改为经原生 bound MCP、本树独立索引、实际 provenance 核验后的条件使用；旧版继续禁用，必需能力不满足时阻断。
- 固定原生手册到已实现并专项测试的 1.6.2-pennix.4；安装版本与手册版本分别核验。
- 明确 Teamwork 只读证据与完整结果包的 Paseo 工作树实施职责；入口由 Trellis bundled Skill 维护，不在全局集合复制协议。

## 验收标准（Acceptance Criteria）

- [ ] 集合清单和回归通过，Skill frontmatter 检查通过。
- [ ] 固定提交交由 Lifecycle 安装，不修改安装副本。
- [ ] 实际发布、安装与查询在根任务接受后才声明生效。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
