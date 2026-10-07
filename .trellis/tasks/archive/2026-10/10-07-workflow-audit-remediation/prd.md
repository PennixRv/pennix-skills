# 工作流审查修复：生命周期安全与发布完整性

## Goal

根协调任务10-07-workflow-audit-remediation的P1工作包；修复collection/tmux回滚、host gate、readiness和root指引并发布安装；用户本轮明确授权方案补齐后直接推进。

## Requirements

- 本owner范围：collection/tmux失败回滚、unsupported host全部写入口、CCH readiness、auth只读probe、native init root指引、真实源catalog物化；不扩建未经证实候选，不覆写历史reports，保留用户配置/数据。
- 根协调任务版本1为输入，用户最新明确授权方案齐备后直接实施；本任务native seal/approve/start记录该真实依据，不伪造seal后的回复。

## Acceptance Criteria

- [ ] 每条触发补证、正确owner最小修复、负例和质量门通过。
- [ ] 真实提交推送/发布、用户与消费者安装验收、精确清理、归档闭合。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
