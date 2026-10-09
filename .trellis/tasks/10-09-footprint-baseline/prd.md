# Align published workflow component baseline

## Goal

Align catalog FastCtx 0.2.22 and Ponytail 5.1.0 immutable ref, deploy the complete validated collection and verify user baseline.

## Requirements

- Pin FastCtx0.2.22 and Ponytail5.1.0/v5.1.0 in the unique catalog; validate and deploy immutable full collection, preserve other target choices.
- Authorized by the user's explicit full reconciliation request; root plan: /home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-09-workflow-footprint-reconciliation.

## Acceptance Criteria

- [ ] Relevant tests and full installed lifecycle verification pass; source/main pushed, collection integrity matches, staging/retired backups cleared.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
