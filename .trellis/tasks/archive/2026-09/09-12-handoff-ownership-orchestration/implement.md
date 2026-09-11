# Implementation plan

1. Read the current handoff helper, renderer, tests, and routing skill; reuse existing lifecycle event, digest,
   retention, and admission code.
2. Add a thin Trellis ownership command adapter with direct-session and explicit-user guards. Keep OpenViking
   calls outside the adapter and preserve control-only behavior when the semantic gate is unavailable.
3. Add receipt transitions for source retirement, target claim, consume, and archive; validate exact handoff/core/
   generation identity and make retries idempotent.
4. Add tests for old-source fencing, competing consumers, target-without-pointer, claim/consume recovery,
   unsupported archive observation, secret/path rejection, and immutable package behavior.
5. Update routing and handoff Skill instructions, then run the complete local test suite and installer checks.
   Commit and push this repository before changing `/home/penn/.codex`.

## Rollback

Disable only the new ownership orchestration entry points and retain the existing core-only handoff path.
Never remove Trellis task state or OpenViking data as part of rollback.
