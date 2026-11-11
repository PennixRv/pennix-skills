# 实现远程 seed 安装入口

## Goal

使 `pennix-workflow-lifecycle` 的 Stage 0 seed 可以像 AoE 上游安装器一样通过
`curl -fsSL ... | bash` 直接运行，不要求调用者先准备 Pennix Skills 源码；同时保留
本地 checkout 入口、配置/凭据安全和正式 lifecycle 的边界。

## Confirmed facts

- 当前 seed 位于 `skills/pennix-workflow-lifecycle/scripts/seed-arch.sh`，模板位于相邻
  `templates/`，所以本地调用成立但 pipe 调用不成立。
- `curl | bash` 会让脚本的标准输入承载脚本内容；seed 的用户输入必须显式从 `/dev/tty` 读取。
- `templates/config.toml.seed` 已包含 `default_mode_request_user_input = true`，
  `auth.json.seed` 是 API key 的唯一 seed 物化位置。
- 正式 lifecycle 的组件版本和 refs 只允许来自
  `skills/pennix-workflow-lifecycle/references/component-versions.json`。
- seed 仅建立 Codex + 基础配置的可启动状态；完整组件 profile 由安装 Pennix Skills 后的 lifecycle
  入口执行。

## Requirements

1. 远程执行时通过固定的 raw GitHub base URL 获取两个静态 seed 模板，不 clone、不 checkout、
   不执行远程源码或 lifecycle 代码。
2. 本地 checkout 执行时继续使用相邻模板，避免维护两份模板内容。
3. 远程/pipe 模式从 `/dev/tty` 询问 `base_url` 和隐藏 API key；没有 TTY 时明确失败。
4. 保留现有 Arch 原生/WSL2 检查、Codex package 安装、冲突 owner 拒绝、已有配置拒绝、原子写入、
   `0600` 权限和失败清理。
5. 输出只告诉用户如何安装 Pennix Skills 并进入 lifecycle，不执行正式 lifecycle 或项目初始化。
6. 补充 remote fixture、pipe input、无 TTY、模板获取失败和 secret non-disclosure 测试，更新 README
   与 `SKILL.md` 的唯一安装入口说明。

## Acceptance Criteria

- [ ] `curl -fsSL https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/scripts/seed-arch.sh | bash` 是文档中的首选入口。
- [ ] 本地 checkout 和 remote fixture 均能生成正确的 config/auth；API key 不出现在 stdout/stderr/config。
- [ ] pipe 输入不消费脚本内容；无 `/dev/tty` 时在任何文件或 package 写入前失败。
- [ ] 已有配置、冲突 Codex package、非 Arch/WSL1、模板下载失败均保持 fail-closed。
- [ ] seed 测试、完整 lifecycle 测试、bash/Python 检查通过。
- [ ] 文档清楚区分 seed 与正式 lifecycle，且没有复制组件版本值。

## Out of scope

- seed 不安装全量 workflow profile，不安装或升级 Trellis/FastCtx/CodeGraph/AoE 等组件。
- seed 不创建项目级 `.trellis/`、`codegraph.json`、AoE project assets。
- seed 不接管用户级 AGENTS.md，不改变用户已有 config/auth，不创建第二个 catalog。
