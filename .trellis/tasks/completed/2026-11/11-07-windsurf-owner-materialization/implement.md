# 有序物化计划

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"materialize","target":{"repository":"pennix-skills","branch":"main","component_or_path":"collection.json; skills/pennix-windsurf-code-search"},"depends_on":[],"action":"等待真实 Windsurf 发行通过，固定完整提交并按既有 npm-pack 流程物化，核对全部字节。","deliverables":"固定源声明和生成快照。","verification":"collection.py sources/verify、完整快照比较及受影响测试。","risks":"源候选或生成工具漂移。","rollback":"恢复旧 pin 并重新生成，不手改物化文件。"},{"id":"deliver","target":{"repository":"pennix-skills","branch":"main","component_or_path":"collection source commit"},"depends_on":["materialize"],"action":"复核后提交推送，交由根任务与 lifecycle 消费。","deliverables":"已验证公开提交、任务收尾。","verification":"远端提交与本地一致。","risks":"消费版本不一致。","rollback":"消费前停止；已消费时以新提交纠正。"}],"stop_point":{"condition":"已验证集合提交可消费且任务原生收尾。","observable_evidence":"源 pin、完整字节比对、测试和远端提交。","remaining_work":"根任务负责生命周期发行、本机安装、全量验收和备份清理。"}}
```
