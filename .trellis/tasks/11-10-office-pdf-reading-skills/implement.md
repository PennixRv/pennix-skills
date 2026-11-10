# WP1 执行合同

当前目标仓库 pennix-skills，分支 main。先引入上游，再适配与验证，再推送源码供 Lifecycle 固定；根任务负责正式发布、安装与组合验收。用户已批准同一整体方案，原生 seal/approve 仅承接真实授权。

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"import","target":{"repository":"pennix-skills","branch":"main","component_or_path":"skills/{docx,pdf,pptx,xlsx}, collection.json"},"depends_on":[],"action":"从固定上游归档引入四项及许可，核对第三方声明，登记主集合并记录来源。","deliverables":"四项原名目录、UPSTREAM.md、许可和 collection.json。","verification":"逐文件来源比较及 collection.py verify。","risks":"来源漂移与不适用第三方内容；仅取固定子目录并核对实际资产。","rollback":"撤销本任务新增目录和清单差异，保留无关内容。"},{"id":"adapt","target":{"repository":"pennix-skills","branch":"main","component_or_path":"四项 SKILL.md、soffice.py、workflow-routing 参考"},"depends_on":["import"],"action":"适配默认只读、运行时、路径及临时目录，移除绕过分支，补最小路由参考。","deliverables":"阅读入口与本地适配。","verification":"必要脚本回归、路径与来源检查、现有集合测试。","risks":"误写原件或运行时不匹配；只读入口不调用 save/recalc。","rollback":"保留固定来源和 diff，恢复对应本地修改。"},{"id":"deliver","target":{"repository":"pennix-skills","branch":"main","component_or_path":"任务记录、源码提交"},"depends_on":["adapt"],"action":"记录验证及规范判断，提交推送给 Lifecycle 固定；根任务继续真实安装验收。","deliverables":"可核验源码提交和组件任务记录。","verification":"源码测试通过，远端 SHA 一致，根集成核验。","risks":"静态验证不代表模型发现或运行时完成，分别记录。","rollback":"Lifecycle 沿原生固定来源恢复旧集合；组件源码通过正常反向提交恢复。"}],"stop_point":{"condition":"WP1 完成并推送，根任务已获得精确源码身份。","observable_evidence":"集合与脚本检查、远端提交及根任务验证记录。","remaining_work":"本组件无剩余实施；真实安装及组合验收由根任务继续。"}}
```
