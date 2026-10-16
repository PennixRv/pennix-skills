# grill 最终方案复核与合并推进确认

## Goal

落实根任务 planning-preseal-review 已展示并明确批准的 Skill 修订范围：先展示完整方案再询问封口并批准推进或补充，同步路由授权判定与生命周期 catalog 发布落点。

## Requirements

- 在 grill 明确先展示最终方案，再征询封口并批准推进或补充修改；普通设计答复不授予实施权。
- 同步 workflow-routing 对同一已展示方案的合并授权判定，保留宿主交互、分析任务、恢复和在途小增量边界。
- 必要发布后更新唯一 lifecycle catalog 的 Trellis 落点，并通过原生集合安装与接纳更新用户副本。

## Acceptance Criteria

- [ ] 两个 Skill 语义一致，补充、仅封口、失败及恢复的行为明确。
- [ ] 现有合同检查与 Skill 校验通过。
- [ ] 源码推送、必要 catalog 更新及原生安装 verify 完成。

## Notes

- 授权来自用户对根任务完整修订包及本 Skill 范围的明确批准；不泛化到无关组件。
- 根协调：`/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-16-planning-preseal-review`。
