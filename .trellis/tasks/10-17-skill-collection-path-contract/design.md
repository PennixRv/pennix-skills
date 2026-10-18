# 技术设计

状态：根任务扩围后重新规划，尚未封口本修订。

集合仓库维护自身 manifest 和静态验证，定义成员/物化来源/命令/引用/许可；工具 catalog 仅固定集合 repo/ref/manifest 位置，避免两份手工成员表和集合 CI→工具→集合的发布环路。同步流程读取自身 manifest，真实来源修复先发布再物化；本集合不执行部署适配器，不把待安装内容当可信验证代码交给工具执行。

Skill 名称是逻辑身份，加载按宿主路径/别名映射，保留集合层级；相对引用以实际 SKILL.md 目录为准。最小规则由 lifecycle 的 AGENTS 来源模板在宿主层维护，routing 解释跨组件职责，lifecycle Skill 不重复定义加载算法。评估记录尝试和成功分别统计，覆盖 extra 集合，避免原正则只认主集合和失败也计入已加载。

更新 README、AGENTS 手工正文、活动质量规范、清理导航与同步/验证入口。当前旧 profile reconcile 规范退出活动合同，历史档案不重写。lifecycle Skill 准确说明独立工具、固定 bootstrap、URL＋Key 认证和当前卸载/归属，不保留旧脚本、模板、catalog、摘要表或 shim。

根任务负责工具模板/用户安装资产、必要来源修复、发布顺序和集成验收；本任务只交付本集合源码、验证与固定提交。

思源连接 owner 管理私有连接记录和 header helper；本机 Codex `mcp_servers.siyuan` 的 URL、header helper 注册由 lifecycle 在其现有 Codex 配置职责内按字段合并并记录可撤回基线。Skill 不增加 Codex TOML writer。连接 receipt 绑定其实际拥有的内容，写入失败恢复本组件修改，外部修改则停止。明确接管仅在输入与现有连接内容一致时成立，不接管任意外部连接。更新测试、Skill 和实际 manifest 来源，Hikari 上游源码及远端服务保持根任务排除边界。
