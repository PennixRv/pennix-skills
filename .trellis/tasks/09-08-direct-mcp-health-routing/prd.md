# Clarify direct MCP health routing

## Goal

Align the Pennix routing guidance with direct MCP service calls and report missing current-session tools without shell HTTP fallback.

## Requirements

- Add one routing rule for configured-service health checks, bounded queries,
  and reads: use the callable MCP tool bound to the current session.
- If the tool is not bound to the current session, report the capability gap
  and stop; do not substitute shell HTTP or invent a schema probe.
- Keep this as routing guidance only; do not add configuration, retries,
  provider logic, or service-specific behavior.
- Keep the wording consistent with context-mode's direct-protocol redirect
  guidance.

## Acceptance Criteria

- [ ] The routing table states direct MCP precedence and the missing-tool stop
      condition.
- [ ] No other Pennix Skill or installer behavior changes.
- [ ] Markdown and repository diff checks pass.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
