# Worktime Memory

## Confirmed Contract

- 用户否决了 runtime bundle、持久 source checkout 和 isolated lifecycle bridge。
- seed 完成后使用 Codex 内置 `$skill-installer` 一次安装完整 collection；下一
  Codex turn 才直接调用 `$pennix-workflow-lifecycle`。这是 Skill 发现时机，不是
  两个部署阶段。
- seed 必须可重入：保留已有 config/auth，补齐单个缺失文件，不覆盖凭据。

## Evidence

- `$skill-installer` 支持公开 GitHub、多个 path 和 destination，但仅作为 agent
  系统 Skill 存在；`openai-codex-bin` 没有对应 shell 子命令或打包脚本。
- `pennix-skills` 的两个 submodule 不能由父 GitHub archive 递归交付，需从其
  owning repository 安装。

## Main Branch Audit

- 已在 `main` 上审计本地与远程分支并合入 `origin/task/openviking-handoff-source-observation` 的有效 OpenViking checkpoint 改动。
- 唯一仍未合入 `main` 的 `task/fastctx-guidance-skills` 是旧设计，重新引入已退役的
  `pennix-fastctx-setup`；它不是当前缺失改动，不应合并。
- 当前 Seed 合同是同一 Codex 会话的两轮对话：第一轮只安装 lifecycle bootstrap，
  第二轮继续同一会话调用 lifecycle；不得写成两个会话或两阶段部署。
