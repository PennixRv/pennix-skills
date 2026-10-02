# 验证与交付

2026-10-02：handoff Python 回归 28/28，lifecycle 回归 132/132；四个修改的 Skill 通过 quick_validate，diff --check 通过。补充 MCP 卸载归属保护后单测再次通过：含无关文件的目录拒绝删除，且不执行配置变更。

源配置已在本机原生执行：固定官方 @agentmemory/mcp 与 @agentmemory/agentmemory 0.9.29，Node --env-file 读取私有客户端配置，关闭插件浮动 MCP。无继承环境的 stdio initialize/tools.list 实测 54 个中心工具。官方 hook 脚本带 env-file 的 canary 已注册当前真实会话并捕获实际验证结论；当前旧宿主没有客户端环境，自动事件只能在正确父环境的新宿主验收。

不声称 FORCE_PROXY 保证失败关闭，也不声称 upstream recall/consolidation 提供项目隔离。重要交接使用明确项目的 REST 精确证明，未知写入结果不盲目重复 POST。

修复提交 4223cb9 已推送并通过 system skill-installer 与 replace-staged 重装完整集合，discover 显示 collection_integrity=match、staging=none。Trellis beta.23 的公共 npm 指定版本与 beta tag 已通过原生 release-preflight 核验；catalog 与既有版本断言同步更新为 beta.23。

后续交付：提交推送 catalog 后重装最终集合，原生升级 Trellis、verify、根消费者升级和真实无任务交接后记录最终结果。
