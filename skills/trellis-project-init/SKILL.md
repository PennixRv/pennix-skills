---
name: trellis-project-init
description: 在项目根目录初始化 Trellis 时使用。执行标准 Trellis 初始化；在派发工作节点前确认项目已经初始化。
---

# Trellis 项目初始化

仅执行标准 Trellis 初始化。该 Skill 不安装插件、不写入项目治理覆盖段，也不维护第二套调度或生命周期实现。

运行确定性入口，不手工拼接初始化或 Bootstrap 命令：

```bash
python3 "$CODEX_HOME/skills/trellis-project-init/scripts/initialize_project.py" \
  --project-root <absolute-project-root> --mode trellis-only
```

可追加 `--developer <name>` 或 `--dry-run`。该入口固定使用
`trellis init --yes --codex --workflow channel-driven-subagent-dispatch --skip-existing -u <developer>`，
从不使用 `--force`，不派发真实 worker，也不读取或输出配置正文、凭据、缓存、会话或运行时状态。

初始化结束后，将项目的 `.trellis/workflow.md`、`AGENTS.md` 和 `.agents/skills/` 作为项目的具体操作规范。项目需要更具体的文档约束时可以覆盖全局
`$trellis-project-document-governance`，但不得删除其结构检查与主会话语义审查边界。
