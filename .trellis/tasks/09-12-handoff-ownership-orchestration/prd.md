# Integrate ownership-aware Pennix handoff orchestration

## Goal

Integrate the Pennix session handoff skill with the Trellis ownership transfer primitive, including source retirement, successor claim, consume/archive receipts, idempotent recovery, and static host deployment documentation. Do not implement a second task ledger or modify OpenViking.

## Requirements

- Extend the existing `pennix-session-handoff` lifecycle without changing the immutable core package
  format or implementing a second task ledger.
- Orchestrate source finalization, Trellis ownership retirement, target admission, successor claim, consume,
  and retention archive as distinct operations.
- Carry only bounded, non-secret receipt metadata: handoff/core digest, source/consumer identity, generation,
  event id, state, and timestamps.
- Treat OpenViking recall/archive as semantic evidence only; do not call Plugin private state, infer task
  authority from memory, or make unsupported archive claims.
- Keep initial target intake read-only: validate, read the paired prompt, run `$trellis-start`, reconcile,
  and stop. Claim requires subsequent explicit user authorization and does not execute the pending action.

## Acceptance Criteria

- [ ] Existing handoff packages validate and render unchanged; core and prompt remain immutable.
- [ ] The skill invokes Trellis ownership operations rather than editing task pointers or duplicating Trellis state.
- [ ] Source retirement, target claim, consume, and archive/retention have distinct receipts and idempotent retry behavior.
- [ ] Old source identity and wrong consumer are refused; unsupported OpenViking archive evidence is returned as
  withheld/unsupported rather than promoted to ready.
- [ ] Runtime receipts are bounded, gitignored, secret-safe, exact-handoff scoped, and purge does not touch tasks,
  OpenViking sessions, memory, resources, or watches.
- [ ] Tests and static checks pass; installation updates the user-level source only through the explicit installer workflow.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
