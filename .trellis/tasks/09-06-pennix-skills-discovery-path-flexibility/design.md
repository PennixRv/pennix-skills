# 设计

## 边界

源码 checkout 是唯一权威；安装目标只是可替换的交付副本。安装器的目标形状仍限制为
`.../skills/pennix-skills`，从而既支持不同宿主根，也保持集合边界。此任务不改变 Codex 或
Trellis 的发现实现。

## 合同

- 默认：`${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills`。
- 显式替代根：调用方传 `--dest <.../skills/pennix-skills>`。
- 直接命令：`${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}`。
- `PENNIX_SKILLS_ROOT` 不被安装器读取；它不创建、探测或持久化宿主根。

## 回滚

还原本仓库的实现提交，并从明确 checkout 重装；不删除任意用户目录。
