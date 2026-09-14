# pennix-skills

这是用户自维护工作流 Skill 的源码仓库。

- 每个 Skill 只维护自身的 `SKILL.md`、脚本、引用资料、测试和必要的界面元数据。
- `skills/windsurf-code-search` 是独立 `windsurf-code-search` 仓库的 Git submodule；它继续拥有
  CLI、测试和 npm 发布，本仓库只固定其组合版本和统一安装说明。
- Trellis 通用 runtime 和 bundled Skill 由 Trellis 组件仓库维护，不在此复制。
- 项目初始化由 Trellis 原生 `trellis init` / `trellis workflow` 完成；本仓库的 `pennix-trellis-setup` 可选择已发布、固定版本的 Pennix Codex workflow 作为默认用户偏好，但不维护初始化器或运行时协议副本。
- 不保存项目任务事实、会话、凭据、缓存、Plugin 物化目录或运行时状态。
- 安装副本由 `pennix-skills-install` 在用户明确请求时写入发现路径；不要在安装副本上形成
  第二个源码权威。安装器不得新建源码 checkout、切换分支、选择版本或更新已固定的组件版本；
  初始化缺失 submodule 时只能取得当前组合 Gitlink 固定的提交。
