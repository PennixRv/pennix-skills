# 切换到独立 Pennix Lifecycle 工具

## 目标（Goal）

删除旧生命周期执行器、种子和重复清单，将 Skill 收敛为新 pennix 工具的入口与边界说明。

## 需求（Requirements）

- 将安装副本的 lifecycle Skill 收敛为新工具 `pennix` 的入口、配置、秘密、卸载、验证和职责边界说明。
- 删除旧的 `lifecycle.py`、`seed-arch.sh`、旧适配器、旧 catalog、旧模板和旧暂存/receipt 合同，不保留兼容入口。
- 说明两阶段路线：基础准备脚本只准备 Arch、Python、Kconfiglib、tomlkit 与用户级 npm 基础；`pennix` 负责配置与生命周期动作。
- 说明 `workflow.config` 为 Kconfiglib `.config` 主版本格式，组件选择与自定义路径/数据分开；秘密由 `pennix secrets edit` 明文维护在私有 `secrets.toml`。
- 说明 `uninstall` 不修改配置；永久取消通过编辑配置后 `pennix apply`；反向依赖和无法撤回的远端 relay 条目必须阻塞。
- 说明集合、Codex TOML、AGENTS、tmux、npm prefix、Paseo 自启动和 relay 的 owner 边界，禁止 Skill 自行执行组件协议。

## 验收标准（Acceptance Criteria）

- [ ] 活动 Skill 不再引用旧命令、旧脚本、旧 catalog、旧暂存或旧状态路径。
- [ ] 新入口示例覆盖无 TTY 配置式部署、交互式配置、计划、执行、检查和显式卸载。
- [ ] 删除范围内文件不存在于源码和活动文档，Skill 仓库测试与 Markdown 检查通过。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
