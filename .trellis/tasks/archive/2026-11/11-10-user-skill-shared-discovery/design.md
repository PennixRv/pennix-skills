# 实施设计

沿用根任务已批准的共享集合方案。在现有 `source_identity` 中将配置根与共享集合 target 分别记录；默认集合读取当前用户 HOME 的 `.agents/skills/pennix-skills`，测试通过显式用户根隔离，不通过 CODEX_HOME 推断集合版本。继续用既有 app-server/exec 采集器，禁止复制认证和模拟成功回执。

路由说明使用准确共享路径实例，同时明确宿主声明是加载依据，system、插件、项目及原生 owner 的必要例外保留。行为来源是完整声明路径、首次实际读和结果；第一次失败不被重试抹掉。原始会话只保留私有临时目录。

根任务的已批准方案、`implementation-authorization.md` 及当前用户明确纠正共同构成展示与实施授权依据。本组件不重新设计取舍。
