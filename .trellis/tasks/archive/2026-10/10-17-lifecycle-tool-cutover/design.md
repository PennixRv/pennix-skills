# 设计

新生命周期工具独立于 Skill 集合发布。Skill 只解释如何选择 `pennix` 原生入口，不复制 catalog、owner 适配器、模板或安装逻辑。基础脚本完成主机和 Python/npm 前置准备后，`pennix config init|edit|check` 负责 Kconfig 模型，`pennix plan|apply|status|check` 负责声明式收敛，`pennix secrets edit` 负责本地可见的秘密填写。

删除旧执行器和旧资产属于破坏性切换。安装副本不再识别旧 profile、旧 receipt、旧 staging、旧 seed 或旧命令；现有用户状态由新工具在独立任务中按 owner 证据处理，Skill 不提供迁移分支。

集合来源、版本和物化由独立工具的固定 catalog 负责。集合 Skill 自身只保留行为合同和实际入口描述，不能通过 `skill-installer` 多轮引导安装，也不能让 Agent 代填模板或命令。
