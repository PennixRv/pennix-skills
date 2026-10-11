# 外部 Bootstrap 模式调研

## 已核验来源

- [chezmoi apply](https://www.chezmoi.io/reference/commands/apply)：以目标状态和差异为中心，支持 `--dry-run`/diff；目标文件被用户修改时会提示，状态和源仓库用于恢复，但没有通用的专用 rollback 命令。
- [mise bootstrap](https://mise.jdx.dev/bootstrap.html)：将机器初始化拆成显式的 dry-run、apply 和 status；`--yes` 只是跳过确认，dry-run 不执行 hooks/final task，新 shell 才获得激活后的环境。
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills)：入口保持简短，确定性逻辑放入 scripts，较深资料按需放入 references；Skill 通过 `SKILL.md` 被发现。
- [Claude Code Plugins](https://docs.claude.com/en/docs/claude-code/plugins.md)：临时本地 `.claude/` 与可复用、可版本化的 Plugin 分开；共享能力应有独立 manifest 和可审计的发布边界。
- [Pi packages](https://pi.dev/docs/latest/packages)：package 可以组合 skills、extensions 和 prompts，但安装具有完整系统权限；第三方 package/source 必须先审阅。

## 采用到 Pennix 的结论

1. `discover`/`plan` 应输出目标状态差异，而不是只列出“要运行的命令”；每个 action 必须带 owner、scope、risk、precondition、postcondition 和 rollback receipt。
2. dry-run 必须真正只读：不执行 hooks、final task、下载、初始化或项目索引；`apply` 只能执行本次明确选择的具名 action。
3. bootstrap Skill 负责用户入口和路由，确定性逻辑放在内部 adapter；adapter 继续调用组件原生 owner，不复制 Trellis、FastCtx、CodeGraph 或 Codex 的生命周期。
4. Pennix 额外保留 receipt/hash 保护的 rollback，因为外部模式通常依赖源仓库或状态库，不能保证只撤销本次变更。
5. 版本、来源和验证键使用 JSON 静态 catalog，避免为读取 catalog 引入 YAML 依赖；用户文案和 adapter 只引用 component key。
6. 安装第三方组件前必须显示 source/ref 和权限边界；密钥、运行态、缓存和完整配置只做存在性/健康检查，不进入 inventory 或 receipt。
7. 成功后必须提示重启或新会话条件；激活后的环境不能用当前 shell 的退出码替代新会话验证。
8. Codex 官方 CLI 将 feature 变更收敛为 `codex features list`、`codex features enable <feature>` 和
   `codex features disable <feature>`；Pennix 的 config adapter 只能在白名单内调用这些原生命令。

## 不采用

- 不引入新的包管理器、常驻 daemon 或全局 profile 管理器。
- 不把 `chezmoi`/`mise` 作为 Pennix runtime 依赖；它们只作为目标状态、dry-run、显式 apply 和激活边界的设计参考。
- 不把 Pi/Claude 的完整 package/plugin 权限模型复制到 Codex；Pennix 仍以当前 Codex Skill discovery 和组件原生 CLI 为 owner。
