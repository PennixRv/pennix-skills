# Handoff lifecycle and retrieval routing remediation

## Goal

Correct Pennix handoff source proof and exactly-once lifecycle behavior, and align web retrieval defaults with the routing contract.

## Requirements

- Keep the immutable handoff core and append-only local lifecycle receipt as
  the only handoff state authorities.
- Correct source-readiness proof so the package is not admitted merely because
  a boundary was sealed when the selected mode requires capsule, archive, or
  convergence evidence.
- Preserve exactly-once logical admission: incomplete consumption is retryable,
  a completed admission is idempotent for the same direct target and rejected
  for another target.
- Keep source retention archive, target ownership archive, and compaction
  recovery distinct; do not add arbitrary package length, SHA, or a new
  permission model.
- Make the retrieval skill's automatic provider behavior match the routing
  contract: Grok first, one explicitly configured fallback only when needed.

## Acceptance Criteria

- [ ] Regression tests cover proof normalization, required-mode readiness,
  incomplete/retryable admission, same-target idempotency, and cross-target
  rejection.
- [ ] Handoff skill documentation accurately describes the lifecycle and
  compaction distinction.
- [ ] Retrieval defaults do not silently start extra providers against the
  routing contract; explicit fallback remains available and observable.
- [ ] Existing handoff and retrieval tests pass, with no secrets or runtime
  artifacts added to the repository.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
