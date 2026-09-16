# OpenViking Handoff Source Observation

> **Superseded for implementation.** Use `checkpoint-decision.md`; this earlier
> draft incorrectly made the source checkpoint depend on a SessionEnd Hook.

## Goal

Add a minimal official OpenViking CLI-backed source arm/finalizer path for
Pennix formal handoff archive and asynchronous extraction convergence. Use a
separate native Codex `SessionEnd` Hook as the only source-end signal; preserve
existing Trellis ownership and make target intake truly all-or-nothing.

## Requirements

- Add `openviking-arm` after `prepare -> quiesce -> seal`. It records a local
  intent with the source Codex id, matching direct Trellis context, and the
  official `ov session get` commit-count baseline.
- Add a finite finalizer invoked by a small user-level `SessionEnd` Hook
  handler. The handler receives the native event, matches an armed source id,
  and otherwise does nothing. The finalizer reads only `ov session get` and
  `ov ls`; it does not call shell HTTP, `ov session commit`, delete,
  import/export, or Plugin-private state files.
- Derive the source OV id exactly as the official Codex Plugin does:
  `cx-` plus the Codex session id with non `[A-Za-z0-9._-]` characters replaced
  by `_`.
- A high-assurance observation requires a matching SessionEnd witness and an
  official commit strictly newer than the post-seal arm baseline. It must use
  the matching newest archive, and may treat `.done` plus `memory_diff.json`
  from that archive as convergence.
- Produce the existing observation schema for the generic lifecycle `finalize`;
  source ownership retirement remains the existing Trellis operation after
  receipt success. Do not add hash/checksum/length gates, new configuration,
  or a scheduler/daemon.
- Change target admission so incomplete consumption writes no attempt/target
  reservation. Full core/prompt read, Trellis startup, fact reconciliation,
  lifecycle readiness, and ownership `ready` are required for its one success
  receipt.
- A target supplied with one exact handoff may preflight readiness and recover a
  failed finalizer only from the matching native witness. It cannot scan for
  handoffs, manufacture a source-end event, consume a pending package, or use
  its own identity to retire the source.

## Acceptance Criteria

- [ ] The arm/finalizer path emits a local observation file compatible with
      `workflow_contracts.validate_observation` only after the native source-end
      witness and a post-arm public commit.
- [ ] High assurance becomes `archive_verified` only with a closed source
  archive, and `converged` only with `.done` plus `memory_diff.json`.
- [ ] `core_only` does not require an OpenViking observation.
- [ ] Missing CLI, failed CLI, absent source, an isolated threshold-only commit,
  absent native witness, and incomplete archive produce explicit non-success
  states without mutating remote state or retiring source ownership.
- [ ] The reviewed Hook fragment is valid native Codex JSON and its handler
  starts no work for unrelated projects/sessions/handoffs.
- [ ] Partial target admission does not reserve a target; complete intake is
  exactly once for the successful target and target compaction/resume does not
  reconsume it.
- [ ] Existing handoff test suite and new focused tests pass.
- [ ] Documentation states source/target session separation, Plugin/Hook
      responsibility, recovery behavior, and that the user must approve the
      new Hook in Codex `/hooks` after deployment.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
