# Remove deployed memory base and active Pennix integration

## Goal

Execute approved root cognee-memory-base-removal plan: native retirement, local handoff, remove active integration and publish clean Skills collection

## Requirements

- Root coordination task: `/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-04-cognee-memory-base-removal`. Its sealed plan was approved for implementation on 2026-10-04.
- First complete receipt-aware native retirement; then delete the dedicated skill, deployment/client, lifecycle catalog/adapters and active routing descriptions.
- New formal handoffs use local core/receipt/ownership contracts; archived formats remain readable without service calls or promotion of missing proof.
- Publish and install the clean collection through native staging. Preserve other tools, credentials, history and user configuration.

## Acceptance Criteria

- [ ] Native retirement removes owned private configuration and optional profile targets without touching unrelated state.
- [ ] No active integration or base description remains; local handoff and lifecycle regressions pass.
- [ ] Source commits pushed, collection installed and verified; closure evidence recorded.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
