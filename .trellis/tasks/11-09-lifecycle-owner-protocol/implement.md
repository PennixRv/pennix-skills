# 实施与交付

1. 阅读各 owner 校验/写入/恢复和测试入口，审定隔离；先修原生实现。
2. 实现 validate、协议及 Grok 外部配置保护，运行定向 Python/Node 回归。
3. 等 WP-W 精确包可用后刷新来源与运行包投影，对比完整字节集合并运行 collection verify/全部必需回归。
4. 集合源码与任务提交推送，由根侧按固定提交发布身份、Lifecycle 升级及本机验收。
5. 原生任务归档、Git 收尾；根仓只固定验收 gitlink 和脱敏证据。

门禁失败、来源或响应身份未知停止依赖操作；不读写真实凭据、远端服务或用户安装副本源码。停止点为根合同规定的发布、本机验收及干净 Git，源码完成不是整体终点。

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"owners","target":{"repository":"pennix-skills","branch":"main","component_or_path":"skills/*/scripts/connection.py与Grok原生脚本"},"depends_on":[],"action":"实现原生预检/事实协议和外部配置保护","deliverables":"原生实现与隔离回归","verification":"各owner定向Python/Node回归与集合完整测试","risks":"秘密、共享字段及归属不明不能覆盖","rollback":"原生前值恢复，未知保留"},{"id":"projection","target":{"repository":"pennix-skills","branch":"main","component_or_path":"collection.json与Windsurf运行投影"},"depends_on":["owners"],"action":"消费WP-W精确公开包刷新投影并提交推送","deliverables":"固定来源、完整字节摘要与根安装证据","verification":"collection verify、包投影对照及本机核验","risks":"上游未发布或身份不符时停止","rollback":"保留旧精确来源，不手补投影"}],"stop_point":{"condition":"固定集合发布身份、根本机验收及Git收尾完成","observable_evidence":"提交/投影/安装身份一致，Git干净","remaining_work":"真实双平台新机和未实测外部服务按根D08保留"}}
```
