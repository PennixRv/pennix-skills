# 实施顺序与停止点

1. 修改既有 routing 路径实例及 evaluation 的来源身份合同，补相应测试。
2. 运行 evaluation 单元测试、routing 合同测试、集合校验和必要 spec 检查。
3. 提交推送来源；由 Lifecycle catalog 固定此提交，原生部署后运行真实读取及 resume/compact 验收。
4. 将核验结果回写本任务，完成组件及根侧 Git 收尾后归档。

唯一正常停止点：来源、安装和真实行为证据一致且根组合验收通过。路径、归属、摘要或首读失败则停止受影响场景并修正，不以干净 Git 或方案批准宣称交付完成。

2026-11-10：规则、来源身份及原生 app-server 声明/读取顺序观察已实施；evaluation 15 项、routing 合同 5 项、集合校验（15 Skills、2 commands）和差异格式检查通过。来源先提交供 Lifecycle 固定；实际安装、默认根发现及 resume/compact 证据由根任务协调后补录。

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"source","target":{"repository":"pennix-skills","branch":"main","component_or_path":"skills/pennix-workflow-routing、evaluations及相关spec"},"depends_on":[],"action":"适配共享目录规则和既有来源评估","deliverables":"规则、评估、测试和来源提交","verification":"routing合同、evaluation单元测试、collection verify及根真实行为验收","risks":"目标、receipt或首读不符不得通过","rollback":"由Lifecycle保留既有固定来源和可信恢复证据"}],"stop_point":{"condition":"固定来源、原生安装、真实行为及Git收尾完成","observable_evidence":"提交、target、digest和原生读取一致；根组合验收通过","remaining_work":"未实测平台和其他宿主依原生支持矩阵单列"}}
```
