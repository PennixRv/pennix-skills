# Lifecycle 连接 owner 合同收敛

## Goal

实施根任务 `lifecycle-audit-findings-convergence` 已展示并获用户“批准并完整推进到全部完成”的 WP-S。完整合同为 `../.trellis/tasks/in_progress/11-09-lifecycle-audit-findings-convergence/implementation-contract.md`，授权为同目录 `implementation-approval.md`。本任务复用该明确批准的组件范围，不重新选择产品路线。

## Requirements

- SiYuan、Hikari、Grok/Grok-Tavily 原生入口新增零副作用 validate 与可信执行结果协议；复用格式/路径/归属规则。
- Grok 部分外部配置不再误判 missing，保护另一目标及外部字段；两种目标都覆盖。
- Windsurf 只从真实 owner 验收后的精确公开包刷新投影、来源和摘要，不独立维护 vendored 源码。
- 完成集合和各 owner 回归、Git 交付，由根侧 Lifecycle 按精确集合提交升级并核验。

## Acceptance Criteria

- 无效输入预检零写入/零网络；可信 none 与未知结果分离，旧调用兼容；秘密只经 stdin，不进入输出。
- 部分外部 Grok/Grok-Tavily 保留；合法两目标配置及撤回不破坏其他目标和用户字段。
- 来源 manifest、完整投影字节与精确包一致，集合 verify 及必需测试通过，根安装验收/Git 收尾完成。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[]}
```
