# Pennix session handoff lifecycle remediation

## Goal

Close the remaining Pennix session-handoff lifecycle gaps in the source Skill:
source readiness must include the canonical JSON/prompt pair, and a target
session must retain one recoverable, ordered consumption attempt before its
single final consumed marker is recorded. The root workflow-audit task remains
the coordination and integration-acceptance record.

## Actual Modification Target

- `skills/pennix-session-handoff/` and its focused tests in this repository.
- The installed copy is updated only after this source task has passed its
  checks and is published through the existing Pennix Skills release path.
- The root repository records receipts only. OpenViking and Trellis source are
  not modified.

## Requirements

- Reuse the existing immutable handoff core/prompt pair and append-only,
  per-handoff lifecycle receipt. Do not add a second task, memory, or state
  database, arbitrary content limit, digest truth gate, or permission model.
- `finalize` must not make the source lifecycle ready until the paired prompt
  is present and readable as well as the selected source boundary/proof mode
  is satisfied. Trellis ownership remains its existing, separate authority.
- A target admission must name its direct `session:<id>` source and progress in
  the documented order: complete JSON core, paired prompt, `$trellis-start`,
  then current-fact reconciliation. A final consumed/reconciled marker is
  written only after all four steps are reported complete.
- A partial intake claims one logical attempt for that same target and can
  resume in place. A different target cannot replace an admitted or reconciled
  target; a blocked source-ready gate does not manufacture a consumption.
- After final consumption, re-entry is idempotent and must not write a second
  consumed marker. Session compaction/recovery remains a current-session
  concern and never calls handoff intake automatically.
- Retention archive remains a later, non-destructive lifecycle phase. Its
  retry path must not re-consume the package or auto-close a task.

## Acceptance Criteria

- [x] Source-ready tests reject a missing paired prompt and preserve the
      existing proof-mode boundary behavior.
- [x] Focused fixtures prove partial intake, ordered in-place recovery,
      cross-target rejection, final exactly-once consumption, and idempotent
      re-entry after a simulated compaction recovery.
- [x] Archive failure and retry are independent of consumption; the core/prompt
      pair and normal Trellis task disposition remain non-destructive.
- [x] Existing proof normalization, ownership fencing, retention and renderer
      regressions still pass.
- [x] Source tests, static Skill checks, source/install revision receipt and a
      focused isolated host exercise are recorded before release.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
