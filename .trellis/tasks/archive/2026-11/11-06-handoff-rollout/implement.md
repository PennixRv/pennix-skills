# 实施与验收

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"fix","target":{"repository":"PennixRv/pennix-skills","branch":"main","component_or_path":"skills/pennix-session-handoff"},"depends_on":[],"action":"先建立真实 CLI 定位回归并确认旧入口失败，再实现只读解析、Skill 指引与复发预防规范。","deliverables":"resolve-rollout 命令、临时 fixture 回归、Skill 与规范。","verification":"定位测试、完整 handoff 测试、collection.py verify、当前线程只读解析。","risks":"Codex SQLite 结构不是跨版本公开合同；身份不匹配时必须拒绝。","rollback":"发布前修正局部差异；发布后新建回退提交，不覆盖无关工作。"},{"id":"release","target":{"repository":"PennixRv/pennix-skills","branch":"main","component_or_path":"组件提交与根协调交付"},"depends_on":["fix"],"action":"审查并提交推送 main；由根任务以 pennix 原生更新安装并核对来源。","deliverables":"发布 commit、安装验收及组件任务归档。","verification":"远端 commit 一致、安装锁/回执与行为一致、根组合验收。","risks":"远端或安装候选漂移时停止。","rollback":"原生生命周期恢复事务；必要时发布回退 commit 后原生更新。"}],"stop_point":{"condition":"组件代码已发布、测试通过且根任务已验收精确安装 commit。","observable_evidence":"测试结果、发布 commit、安装及根验收记录。","remaining_work":"无合同内遗留；未来 Codex 元数据结构变化需重新核验。"}}
```
