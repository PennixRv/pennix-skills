# pennix-skills

这是用户自维护工作流 Skill 的源码仓库。

- 每个 Skill 只维护自身的 `SKILL.md`、脚本、引用资料、测试和必要的界面元数据。
- `skills/windsurf-code-search` 和 `skills/grok-search` 是本集合中的物化 Skill 快照；上游仓库、ref
  和精确提交由唯一 lifecycle catalog 记录，并随集合快照一起更新。
- Trellis 通用 runtime 和 bundled Skill 由 Trellis 组件仓库维护，不在此复制。
- 工作流部署统一由 `pennix-workflow-lifecycle` guided Skill 编排；Trellis 项目初始化仍由原生 `trellis init` / `trellis workflow` 完成，组件适配脚本位于 lifecycle 的 `scripts/adapters/`，不复制初始化器或运行时协议副本。
- lifecycle catalog 只声明配置 target、owner ingress、状态探针和精确来源；profile/collection receipt 只保存私有完整性元数据，禁止共享 `.env`、凭据复制和把 owner 协议交给 FastCtx。
- Trellis task/Channel/handoff、Codex 原生交互、Hook/MCP/TUI 和 owner retrieval 保持原生所有权；`pennix-workflow-routing` 与 `pennix-fastctx-routing` 只做 owner-first 路由，不模拟这些协议。
- 不保存项目任务事实、会话、凭据、缓存、Plugin 物化目录或运行时状态。
- 安装副本由系统 `$skill-installer` 在 Codex 会话中写入发现路径；lifecycle 只编排该原生所有权，
  不要在安装副本上形成第二个源码权威。目标机安装使用系统 `$skill-installer` 的临时 staging，
  不创建源码 checkout、切换分支或目标机 submodule。
