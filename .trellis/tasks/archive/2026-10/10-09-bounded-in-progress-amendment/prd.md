# 在途增量规则与生命周期模板

## Goal

Owner task for the bounded in-progress amendment rule, its contract test, and lifecycle AGENTS template synchronization; coordinated by the root task.

## Requirements

- 将用户明确提出的、同任务同 owner、低风险、可逆且不改变封口范围/验收/发布路径的在途增量定义为可保持 `in_progress` 的边界。
- 要求把请求、分类、owner、验收与验证写入当前任务执行记录；材料变化或无法判断时继续要求 `task.py replan`。
- 同步 lifecycle 安装模板，增加一个最小契约测试，不创建第二套生命周期。

## Acceptance Criteria

- [ ] `pennix-decision-grill` 同时覆盖 bounded amendment 和 material replan 两条路径。
- [ ] 契约测试通过，lifecycle 模板与技能规则语义一致。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
