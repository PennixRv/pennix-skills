# Workflow governance, lifecycle configuration, and routing convergence

## Goal

Implement the approved Pennix workflow-governance convergence across the owner repositories: make lifecycle configuration explicit and reentrant, make collection delivery transactional and pinned, correct decision-gate and FastCtx routing contracts, and materialize only released owner snapshots.

## Requirements

- `grok-search` 与 `windsurf-code-search` 在 owner `main` 上完成安全配置入口、测试和发布；Trellis 只允许其目标 beta 分支，且本任务不创建新分支。
- 将两个 owner release 投影为 collection 中的普通完整 Skill 目录；独立仓库继续是源码 owner。
- `component-versions.json` 是 collection 成员的来源仓库、固定 SHA、安装路径、名称及后置动作的唯一版本/安装事实；不得保留可变 `main` 安装引用或第二个 manifest。
- lifecycle 必须声明 core/optional configuration targets，使用 owner-native terminal/UI ingress、私有 profile 和无 secret 的状态输出；不引入共享 `.env`。
- lifecycle 对 collection 的 install、upgrade 与 reinstall 必须在 staging 中完成原生安装、受限 post-install action 和完整验证后才替换正式安装目录；失败保留旧安装，未知内容不静默删除。
- collection 通过一个来源 `PennixRv/pennix-skills` 交付所有成员；`grok-search` 的 npm 后置依赖安装继续可观察且受测。
- collection 自身提供最小权限的 scheduled/manual 同步工作流：解析两个来源默认分支 SHA、物化普通目录、更新唯一 catalog、验证后创建或更新 PR；不得自动合并或直接写入 `main`。
- `pennix-decision-gates` 必须识别复杂 `analysis_only`，同一 continuation 持久化回答后继续，并在 final seal 消除静态待决策点。
- `pennix-fastctx-routing` 与 `pennix-workflow-routing` 必须 owner-first 排除 Trellis/handoff/Channel/native UI/Hook/MCP/lifecycle 协议；`grok-search` 保持外部检索 owner。
- 同步仓库说明、AGENTS、lifecycle Skill 和测试，删除失效的 submodule 特殊规则。

## Acceptance Criteria

- [ ] 两个 owner 在 `main` 有已验证 commit/tag；Trellis owner 后续只在 `pennix/v0.7-beta` 发布，所有目标分支记录在任务元数据。
- [ ] `skills/grok-search` 与 `skills/windsurf-code-search` 是完整普通目录，不再为 gitlink，GitHub archive 可直接读取其 `SKILL.md`。
- [ ] catalog 对物化成员保存准确、不可变来源 SHA；同步 workflow 以该 SHA checkout，不自动刷新到可变 ref。
- [ ] 配置 profile/receipt 为私有且无 secret；core/selected optional 的 discover/verify、legacy/drift/unknown 保护和 owner ingress 均受测试覆盖。
- [ ] clean install、reinstall、upgrade、staging failure、旧安装保留、drift/unknown-content 保护和 `grok-search` 后置动作均受自动测试覆盖。
- [ ] decision-gate 与 routing contract 测试通过，且 FastCtx 不接管任何专用 owner 协议。
- [ ] 同步工作流 fail closed、只创建/更新 PR、不自动合并；其生成逻辑不引入第二份版本事实。
- [ ] 完整测试通过，变更提交并推送至 `main`，owner 发布后的原生安装路径可重装并通过 catalog/receipt 验证；所有任务静态待决策点已锁定。

## Notes

- Root planning task `09-22-pennix-skills-collection-governance` 保存用户决策与研究证据；本任务是该仓库的实施记录。
