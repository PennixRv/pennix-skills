# 工作期关键决策

## 2026-09-18：Stage 0 认证与调用者提示

- API key 改由 `cli_auth_credentials_store = "file"` 和原生
  `codex login --with-api-key` 写入 `CODEX_HOME/auth.json`；不再创建 `codex.env` 或 shell marker。
- 已有 `config.toml` 或 `auth.json` 都在包安装前失败关闭；登录失败时只清理本次脚本创建的文件。
- seed 完成提示只要求安装 Pennix Skills，然后使用 `pennix-workflow-bootstrap` 开始部署；不暴露
  Stage 编号、source checkout 或内部脚本调用。
- `seed-arch.sh` 设置为可执行 Bash 脚本，可由 bash/zsh 直接调用，但不允许 source；测试覆盖 zsh
  调用时 shebang 选择 Bash 的路径。

来源：本会话用户指令；官方 OpenAI Docs `https://developers.openai.com/codex/auth`、
`https://developers.openai.com/codex/config-reference`。

## 2026-09-18：模板化与分阶段物化修正

- 原生 `codex login`/`codex features enable` 方案已被用户明确 superseded；仓库没有现成模板，需从
  当前 Pennix Codex baseline 提取并纳入 `templates/`。
- seed 只渲染 `config.toml.seed`、`auth.json.seed`；installation 再渲染 `config.toml.install`、
  `AGENTS.md.install`。API key 仅进入 seed 生成的 `auth.json`。
- bootstrap action 明确分为 `system-installation` 和 `project-initialize`；项目初始化不能作为
  系统安装或 Skills 安装的副作用。

## 2026-09-18：可移植基线收敛

- `config.toml.install` 只提取 baseline 的可移植静态策略，使用根级与 `[features]` 两个受控片段
  物化到精确 seed config；不复制主机路径、Web 地理位置、项目 trust、MCP/插件/marketplace 状态或
  hook hash。
- 缺失 `--project-root` 的 project action 必须 `blocked`，不能再隐式使用当前工作目录。
- 隔离验证覆盖 seed → install TOML、模板 drift 拒绝、config/AGENTS receipt rollback、模板目录安装副本；
  46 项测试、source collection check、语法/编译与任务校验均通过。
