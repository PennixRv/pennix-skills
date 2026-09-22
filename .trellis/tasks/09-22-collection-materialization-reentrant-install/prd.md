# Materialize collection skills and reentrant install

## Goal

Implement the approved collection-governance plan: materialize grok-search and windsurf-code-search, make lifecycle install transactional and reentrant, and add catalog-driven sync verification.

## Requirements

- 将 `grok-search` 与 `windsurf-code-search` 从 Git submodule 迁移为提交在 collection 中的普通完整 Skill 目录；两个独立仓库继续是源码 owner。
- `component-versions.json` 是 collection 成员的来源仓库、固定 SHA、安装路径、名称及后置动作的唯一版本/安装事实；不得保留可变 `main` 安装引用或第二个 manifest。
- lifecycle 对 collection 的 install、upgrade 与 reinstall 必须在 staging 中完成原生安装和完整验证后才替换正式安装目录；失败保留旧安装，未知内容不静默删除。
- collection 通过一个来源 `PennixRv/pennix-skills` 交付所有成员；`grok-search` 的 npm 后置依赖安装继续可观察且受测。
- collection 自身提供最小权限的 scheduled/manual 同步工作流：解析两个来源默认分支 SHA、物化普通目录、更新唯一 catalog、验证后创建或更新 PR；不得自动合并或直接写入 `main`。
- 同步仓库说明、AGENTS、lifecycle Skill 和测试，删除失效的 submodule 特殊规则。

## Acceptance Criteria

- [ ] `skills/grok-search` 与 `skills/windsurf-code-search` 是完整普通目录，不再为 gitlink，GitHub archive 可直接读取其 `SKILL.md`。
- [ ] catalog 对全部 collection 成员只使用父仓库安装来源，并为物化成员保存准确、不可变的来源 SHA。
- [ ] clean install、reinstall、upgrade、staging failure、旧安装保留、drift/unknown-content 保护和 `grok-search` 后置动作均受自动测试覆盖。
- [ ] 同步工作流 fail closed、只创建/更新 PR、不自动合并；其生成逻辑不引入第二份版本事实。
- [ ] 完整测试通过，变更提交并推送至 `main`，发布后的原生安装路径可重装并通过 catalog 验证。

## Notes

- Root planning task `09-22-pennix-skills-collection-governance` 保存用户决策与研究证据；本任务是该仓库的实施记录。
