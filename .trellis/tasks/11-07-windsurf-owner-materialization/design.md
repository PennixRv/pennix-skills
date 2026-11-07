# 固定源与物化设计

根合同 revision `24db3ff9e7d997bf2ffcdefb7006894006d980df3382e76b5339d42f16d2e00a` 已获“批准，现在开始吧”授权，覆盖组件提交、推送、安装和收尾。当前 main 基线 `06e4c4e008a6d5dd0f7c14bc92f0b1cda48289b6`；依赖 Windsurf 关联任务的已验证发行，不提前消费候选源码。

collection.json 继续为唯一源清单，npm-pack 生成 Windsurf 快照。按现有 sync-collection workflow 的相同机制物化与比较完整字节；其他成员不变。生命周期导航仅在其公开入口变化确需说明时修改源 Skill。运行 collection verify、集合与相关成员测试，再提交推送供 lifecycle pin。未知生成差异停止，不手工修补快照。

规划审查已核对目标、依赖、兼容、验证和恢复；不新增产品取舍。恢复采用新提交还原源 pin 并重新物化。根任务负责安装及本任务产生的备份清理。
