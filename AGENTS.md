# pennix-skills

这是用户自维护工作流 Skill 的源码仓库。

- 每个 Skill 只维护自身的 `SKILL.md`、脚本、引用资料、测试和必要的界面元数据。
- `collection.json` 是本集合唯一交付清单，拥有成员路径、许可、命令和物化来源；集合验证与同步读取它。lifecycle 只固定本仓库提交并独立验证该清单，不复制成员白名单。
- Trellis 通用 runtime 和 bundled Skill 由 Trellis 组件仓库维护，不在此复制。
- 工作流部署由独立 `PennixRv/pennix-lifecycle` 工具编排；Trellis 项目初始化仍由原生 `trellis init` / `trellis workflow` 完成。本集合不复制生命周期执行器、组件适配器或运行时协议。
- lifecycle catalog 由独立 `PennixRv/pennix-lifecycle` 仓库声明配置目标、组件入口、状态探针和精确来源；本集合只保存 Skill 内容，不复制凭据、组件执行器或状态机。
- `pennix-workflow-routing` 按操作语义选择来源与工具；遵循 Context Mode v2 和宿主的原生输出处理，大输出按需分析，原生工具可作为逐次回退，组件仍拥有自己的协议。
- 不保存项目任务事实、会话、凭据、缓存、Plugin 物化目录或运行时状态。
- 安装副本由生命周期工具按固定 catalog 物化到发现路径；不要在安装副本上形成第二个源码权威，
  不创建源码 checkout、切换分支或目标机 submodule。

<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

For a new session use `trellis-start`; for existing work use `trellis-continue`
and resume the known unfinished action. Read `.trellis/workflow.md` for the
native route and ownership rules. Task CLI owns task and phase state; specs
describe engineering conventions, not implementation authorization.

Without hook context, run `python3 ./.trellis/scripts/get_context.py --mode phase`
and `python3 ./.trellis/scripts/task.py phase show <task>`, then explicitly read
the applicable spec indexes and their referenced guidelines.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — task records and their planning, implementation, and review artifacts

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

Project-scoped helpers use these native owners:
- `.agents/skills/` — reusable Trellis methods
- `.trellis/agents/` — Teamwork role cards and Paseo node methods

The main session owns task decisions and integration. Collaboration uses
`trellis teamwork` or `paseo-based-parallelism` under the authorized contract.

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->
