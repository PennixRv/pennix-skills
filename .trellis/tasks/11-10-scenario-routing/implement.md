# 实施顺序与停止点

1. 修改总路由与按需场景引用、阶段说明，核验 25 项职责覆盖。
2. 扩展既有评估来源、受限案例能力及预算，补行为保护单测和自然场景。
3. 跑集合、路由、评估测试，提交推送 main，交 Lifecycle 固定来源。
4. 实际安装后执行根合同 61 次场景及恢复验收；记录真实失败、修正和限制。
5. 根集成与组件交付均通过后，原生归档并提交收尾记录。

方案已在根任务独立复核并整体批准；本包不扩大成员、运行时、宿主部署、权限或预算。停止点为源码与正式安装身份一致、合同验收及 Git 收尾完成；越权或来源漂移先停止相应案例。

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"routing-evaluation","target":{"repository":"pennix-skills","branch":"main","component_or_path":"skills/pennix-workflow-routing、evaluations及相关spec"},"depends_on":[],"action":"落实25项路由及双集合行为验收","deliverables":"场景引用、评估器、测试和固定来源","verification":"collection verify、路由与评估单测、根真实场景和恢复验收","risks":"来源漂移、误触发和权限扩大不得通过","rollback":"Lifecycle原生固定来源恢复，保留首次失败"}],"stop_point":{"condition":"正式安装、真实行为、根集成和Git完成","observable_evidence":"提交、receipt、digest与真实轨迹对应","remaining_work":"未部署宿主及其他模型不纳入可靠性声明"}}
```
