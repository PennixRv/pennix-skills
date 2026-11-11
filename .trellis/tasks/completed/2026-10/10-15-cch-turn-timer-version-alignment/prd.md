# 同步 CCH turn 计时修复的生命周期版本落点

## Goal

在 CCH 修复发布验收后，仅更新 cch-status 固定版本并经原生 Skill 暂存与集合替换部署，保留其他组件及用户配置。

## Requirements

- 依赖 CCH `10-15-codex-native-turn-timer-parity` 发布并重装验收 `0.1.46`。仅将唯一 lifecycle catalog 的 `components.cch-status.approved_version` 从 `0.1.45` 更新到 `0.1.46`，不更改安装所有权、凭据或其他组件固定版本。
- 在本仓库任务下修改源码 catalog；活动 Skill 集合只能经系统 skill-installer 从已推送精确提交暂存，再以 lifecycle 原生 replace-staged 接纳。不直接编辑安装副本，不采用本地复制或覆盖收据。
- 纳入必要的安全 profile 摘要 reconcile：仅当 discover 报告该目录下现行 profile 因本次 catalog 更新过期，且原生就绪校验通过时刷新摘要，保持 targets 及秘密值不变；未知或漂移即停止。
- 主会话执行，按计划封口、后续明确批准和原生 start 进入实施；不能用根任务或 CCH 单项批准替代本任务当前封口版本的明确批准。

## Acceptance Criteria

- [ ] diff 仅有 CCH 版本字段及本任务资产；catalog 有效，现有生命周期和集合测试通过。
- [ ] CCH Release、实际 CLI/运行态及 catalog 均为 `0.1.46`；源码提交已推送 main，安装来源绑定该精确提交。
- [ ] 暂存集合完整验证，原生事务替换成功，活动集合回执与内容匹配；不改 AGENTS 模板、配置目标、秘密值或其他 Skill 行为。
- [ ] scoped `verify --component cch-status --yes` 及集合核验通过；全量核验如有既存无关失败，明确分开报告，不能宣称整体全绿。
- [ ] 任务记录新旧提交、版本、部署和回退证据，不记录完整运行态或配置正文。

## Notes

- 本次依赖与部署步骤见 design.md、implement.md；保持 planning，当前没有改 catalog 或安装集合。
- 来源基线 `1c1c1a4444bfb2f81ca5343dde3b00c21412bafe` 等于当前远端 main。当前旧分支名不作为新任务分支；批准后将本地 main 仅快进到此基线，在 main 交付。
- 根协调记录：根仓库 `.trellis/tasks/10-15-cch-turn-timer-delivery`。不修改 Trellis 资产、静态用户规则或生命周期实现来掩盖版本漂移。
