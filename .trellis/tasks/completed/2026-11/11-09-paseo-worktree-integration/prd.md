# Paseo 工作树集成的 CodeGraph 与路由合同

## 目标（Goal）

承接已批准 W3，按已验证 CodeGraph bound 接口更新能力条件、原生手册及组件路由；当前主会话实施与验收。

## 需求（Requirements）

- 将绝对禁止 linked worktree 的旧约束改为经原生 bound MCP、本树独立索引、实际 provenance 核验后的条件使用；旧版继续禁用，必需能力不满足时阻断。
- 固定原生手册到已实现并专项测试的 1.6.2-pennix.4；安装版本与手册版本分别核验。
- 明确 Teamwork 只读证据与完整结果包的 Paseo 工作树实施职责；入口由 Trellis bundled Skill 维护，不在全局集合复制协议。

## 验收标准（Acceptance Criteria）

- [x] 集合清单和回归通过，Skill frontmatter 检查通过。
- [x] 固定提交交由 Lifecycle 安装，不修改安装副本。
- [x] 实际发布、安装与查询在根任务接受后才声明生效。

## 本次变更

仅维护已批准 W3 的 CodeGraph 条件绑定、固定原生手册及 Teamwork/Paseo 职责路由；不复制 Trellis 控制面或改变用户全局规则。

## 验证

集合清单与13项合同回归、2项Skill frontmatter检查通过；发布源码d94b1341ba26d6010fd60a3f8f81f7b93c762dba已交原生Lifecycle精确安装，根任务继续核验独立节点真实图能力。

根 W4 已核验两个真实节点读取该安装集合的 CodeGraph Skill，各自原生 bound MCP 查询返回本树 provenance 并拒绝跨树路径；实际进程使用1.6.2-pennix.4。根组合门禁19/19通过，组件条件路由已实际生效；整体委派结果与资源收尾由父任务继续接受。

## 停止条件

旧版、索引或原生bound/provenance未验证时保留保护，不用新版Skill替代能力证明；不改安装副本。

## 回退方案

由Lifecycle沿既有可信集合来源固定原提交，失败保留原生事务及旧集合；不手工修改receipt或缓存。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
