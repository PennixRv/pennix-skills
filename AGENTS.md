# pennix-skills

这是用户自维护工作流 Skill 的源码仓库。

- 每个 Skill 只维护自身的 `SKILL.md`、脚本、引用资料、测试和必要的界面元数据。
- `skills/windsurf-code-search` 是独立 `windsurf-code-search` 仓库的 Git submodule；它继续拥有
  CLI、测试和 npm 发布，本仓库只固定其组合版本和统一安装说明。
- Trellis 通用 runtime 和 bundled Skill 由 Trellis 组件仓库维护，不在此复制。
- 工作流部署统一由 `pennix-workflow-lifecycle` guided Skill 编排；Trellis 项目初始化仍由原生 `trellis init` / `trellis workflow` 完成，组件适配脚本位于 lifecycle 的 `scripts/adapters/`，不复制初始化器或运行时协议副本。
- 不保存项目任务事实、会话、凭据、缓存、Plugin 物化目录或运行时状态。
- 安装副本由 lifecycle 调用内部 Skills deployment adapter 在用户明确请求时写入发现路径；不要在安装副本上形成
  第二个源码权威。安装器不得新建源码 checkout、切换分支、选择版本或更新已固定的组件版本；
  初始化缺失 submodule 时只能取得当前组合 Gitlink 固定的提交。
