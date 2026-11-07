# 实施计划

1. 在 main@5cfe7adb61ddd585a6f65574b5aec6fb1c6c3c49 创建 refactor/context-mode-v2-consumers 分支。读取当前 manifest、路由、CodeGraph、资源清理及评估入口。
2. 删除独立集成成员和其 manifest，修订上述实际引用及测试；保留历史任务证据，不复制上游实现。
3. 修改 runner 的候选环境与固定来源核验，更新受影响 S04、跨组件和路径案例，不重跑无关领域全集。运行集合验证、路由合同和 runner unittest。
4. 等 Lifecycle 候选具备 owner 物化能力后，在隔离 CODEX_HOME 进行固定 before/after 真实评估，记录失败与无法触发项，不复制认证。
5. 审查全部差异与必要 spec，提交源码、任务记账和日志。按根任务既有发布授权合回 main 并公开固定提交，供 Lifecycle 消费。

停止点：集合公开 SHA、owner 安装移除旧成员、受影响真实行为及根集成全部有证据后，才完成组件与根任务的交付审查。当前不满足时只记录精确断点，不提前归档。

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"consumers","target":{"repository":"PennixRv/pennix-skills","branch":"refactor/context-mode-v2-consumers","component_or_path":"collection.json、skills、evaluations"},"depends_on":[],"action":"执行正文步骤 1 至 3：删除集成成员并适配引用与评估。","deliverables":"新 manifest、路由/资源文档及评估接口和测试。","verification":"collection verify、路由与 runner unittest。","risks":"旧引用残留或把 phase 当版本切换。","rollback":"源码回退至 5cfe7adb61ddd585a6f65574b5aec6fb1c6c3c49；不手改安装副本。"},{"id":"delivery","target":{"repository":"PennixRv/pennix-skills","branch":"refactor/context-mode-v2-consumers","component_or_path":"evaluations、任务与发布提交"},"depends_on":["consumers"],"action":"执行正文步骤 4 至 5，依赖 Lifecycle 候选物化与根集成。","deliverables":"固定 before/after 评估证据和公开 SHA。","verification":"真实受影响用例、owner 安装移除旧成员与根集成。","risks":"缺少实际行为证据时不得声明通过。","rollback":"Lifecycle receipt 恢复旧集合。"}],"stop_point":{"condition":"公开集合 SHA、owner 安装和根验收全部通过。","observable_evidence":"提交、receipt、评估与根集成结果。","remaining_work":"停止点满足后无本组件剩余工作；不满足时记录精确断点。"}}
```
