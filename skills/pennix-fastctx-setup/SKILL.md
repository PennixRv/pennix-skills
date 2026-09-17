---
name: pennix-fastctx-setup
description: Explicitly deploy, inspect, migrate, or roll back Pennix FastCtx from a pinned PennixRv GitHub Release. Use only when the user explicitly requests FastCtx installation, upgrade, host migration, or rollback.
---

# Pennix FastCtx 部署

只在用户明确要求安装、升级、迁移、诊断或回滚 FastCtx 时使用本 Skill。普通本地操作由
`$pennix-fastctx-routing` 处理。

从明确版本的 `PennixRv/fastctx` GitHub Release 部署，绝不使用 `latest`、本地构建或未校验资产：

```bash
python3 "/path/to/pennix-skills/skills/pennix-fastctx-setup/scripts/setup.py" doctor
python3 "/path/to/pennix-skills/skills/pennix-fastctx-setup/scripts/setup.py" plan --version v0.2.7
python3 "/path/to/pennix-skills/skills/pennix-fastctx-setup/scripts/setup.py" apply --version v0.2.7 --yes
python3 "/path/to/pennix-skills/skills/pennix-fastctx-setup/scripts/setup.py" rollback --yes
```

- `plan` 只展示将使用的发布资产；`apply` 必须先完成 `doctor` 与 `plan`，并明确传入 `--yes`。
- `apply` 校验 `SHA256SUMS`，用发布二进制先移除其受管的旧 FastCtx marker，再以 `--guidance none` 安装；最后只写入精确的 Pennix FastCtx dispatcher marker 到用户级 `AGENTS.md`。
- 不修改项目 `AGENTS.md`，不复制配置、凭据、会话、缓存、数据库或日志；不得打印环境变量中的敏感值。
- `rollback` 只删除精确的 Pennix marker，再恢复 FastCtx 自己的受管 guidance；不会删除 MCP 配置。
