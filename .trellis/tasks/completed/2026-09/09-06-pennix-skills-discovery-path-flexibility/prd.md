# 放松 Pennix Skills 发现路径约束

## Goal

保留 Codex 默认安装根，同时让 Pennix Skills 安装与直接命令支持显式的兼容集合根；完成回归、发布与重装验收。

## Requirements

- 保留安装器默认目标 `${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills` 及其现有安全校验。
- 允许用户通过 `--dest` 显式选择其他兼容的 `skills/pennix-skills` 集合根，包括
  `.agents/skills/pennix-skills`，但不声称任意宿主会自动发现该路径。
- 让 README、安装 Skill 和所有依赖安装副本的直接命令支持可选
  `PENNIX_SKILLS_ROOT` 集合根；不增加自动探测、第二份源码、持久状态或自动更新。
- 让 `review-gate` 对同一组合内 `evidence-report` 合同的安装副本回退遵循显式集合根。
- 为默认值、显式替代根、非法目标和跨 Skill 回退增加定向验证；提交并推送后重装当前用户集合。

## Acceptance Criteria

- [ ] 不传 `--dest` 的安装器行为与 `CODEX_HOME` 覆盖保持不变。
- [ ] 合法 `.agents/skills/pennix-skills` 目标可完成隔离安装，非法形状及符号链接继续被拒绝。
- [ ] 文档不再将默认 Codex 根称为唯一合法落点，且不将替代根描述为所有宿主的自动发现事实。
- [ ] `PENNIX_SKILLS_ROOT` 只作为直接命令的调用方约定；安装器不读取它或执行发现扫描。
- [ ] 定向测试、源集合 `--check`、临时替代根 smoke test 通过；源仓库提交并推送后重装当前集合。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
