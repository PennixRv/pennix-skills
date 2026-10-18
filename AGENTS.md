# pennix-skills

这是用户自维护工作流 Skill 的源码仓库。

- 每个 Skill 只维护自身的 `SKILL.md`、脚本、引用资料、测试和必要的界面元数据。
- `collection.json` 是本集合唯一交付清单，拥有成员路径、许可、命令和物化来源；集合验证与同步读取它。lifecycle 只固定本仓库提交并独立验证该清单，不复制成员白名单。
- Trellis 通用 runtime 和 bundled Skill 由 Trellis 组件仓库维护，不在此复制。
- 工作流部署由独立 `PennixRv/pennix-lifecycle` 工具编排；Trellis 项目初始化仍由原生 `trellis init` / `trellis workflow` 完成。本集合不复制生命周期执行器、组件适配器或运行时协议。
- lifecycle catalog 由独立 `PennixRv/pennix-lifecycle` 仓库声明配置目标、组件入口、状态探针和精确来源；本集合只保存 Skill 内容，不复制凭据、组件执行器或状态机。
- `pennix-workflow-routing` 与 `pennix-context-mode-integration` 按操作语义选择载体；普通 CLI 可经 Context Mode 执行，宿主 MCP、交互及 continuation 保留原生入口，组件仍拥有自己的协议。
- 不保存项目任务事实、会话、凭据、缓存、Plugin 物化目录或运行时状态。
- 安装副本由生命周期工具按固定 catalog 物化到发现路径；不要在安装副本上形成第二个源码权威，
  不创建源码 checkout、切换分支或目标机 submodule。

<!-- TRELLIS:START -->
# Trellis

Follow `.trellis/workflow.md`; read the applicable `.trellis/spec/` guidance before editing code, and keep task facts in `.trellis/tasks/`. Project-scoped helpers live in `.agents/skills/`.

When a live Trellis Channel wait returns a host continuation, resume only that continuation until it resolves, times out, or errors. Do not run another host action meanwhile, including another wait, shell command, or status/message query; use diagnostics only on demand after it returns.

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->
