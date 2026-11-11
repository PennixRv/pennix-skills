# 收敛 Pennix Workflow Lifecycle 生命周期入口

## Goal

将 workflow bootstrap 入口收敛为 lifecycle，补齐单一 catalog 的组件能力声明、升级/卸载/验证边界、模板与来源固定校验，并保留原生 owner 与项目初始化边界。

## Requirements

- 将公开 Skill、目录、frontmatter、README、AGENTS、routing 和 seed 输出统一改为 `pennix-workflow-lifecycle`；不保留旧业务入口 alias。
- 以 `references/component-versions.json` 作为唯一版本/source ref/template revision catalog；把静态模板、Skills source checkout 和组合 submodule 的父侧事实纳入 catalog，不复制子仓库内部 npm 版本。
- 为每个组件声明 `install/configure/upgrade/uninstall/verify/project_init` 的真实状态：`managed`、`native-owner`、`verify-only`、`project-only` 或 `not-applicable`；入口只执行 `managed` 动作，对其他状态给出可执行原因。
- 保留单组件 `discover/install/upgrade/uninstall/verify`，不引入批量 action、`plan/apply/rollback` 状态机；系统生命周期不得隐式创建项目级 Trellis、CodeGraph 或 AOE 资产。
- 对 managed 静态模板、Skills checkout、插件 ref 和动态上游检查补齐 revision/ref/hash、漂移拒绝、幂等和 postcondition 验证；凭据只做 presence/permission 检查，不写入 catalog、inventory、任务或日志。
- 将 CodeGraph/Trellis/AOE 项目初始化、native plugin、hook migration 等边界明确为 project-only/native-owner/verify-only，不伪装成统一 installer 已经接管。
- 扩展现有 `pennix-decision-gates`，吸收依赖 frontier、分轮批量提问和每轮重算协议；不 vendor 第三方 `grill-me`/`grilling`，不修改 Trellis fork。

## Constraints

- 实际源码仅限本仓库；根仓库只负责任务记录、集成验收和跨仓库事实。
- 不修改 `/home/penn/.codex`、Trellis、OpenViking、FastCtx 或其他组件源码；不执行真实系统安装、升级、卸载或用户凭据写入。
- 保留 Arch Linux 原生/WSL2 的既有 host 边界和最小命令入口，拒绝未知/漂移状态而不是覆盖用户资产。

## Acceptance Criteria

- [ ] 新 Skill 名称和引用收敛完成，旧业务目录/入口不残留，所有现有路由和静态扫描通过。
- [ ] catalog 是版本、source ref、template revision 和 action capability 的唯一静态事实；入口不再维护重复静态组件列表。
- [ ] discover/verify 展示组件 owner、scope、action 状态和 postcondition；managed 与 native-owner/project-only/verify-only 的行为有回归测试。
- [ ] fresh fixture、重复执行、已知旧 managed state、漂移拒绝、精确卸载和 verify missing/match 测试通过；组合 submodule/ref 与动态上游 hash 失败会在写入前停止。
- [ ] `pennix-decision-gates` 的 frontier 批次、依赖延后、决策回写和无阻塞收敛行为有最小测试/静态合同；不引入第三方运行时依赖。
- [ ] `python -m compileall`、项目测试、shell 语法检查和 `git diff --check` 通过；任务记录包含未实施的外部安装/发布边界。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
