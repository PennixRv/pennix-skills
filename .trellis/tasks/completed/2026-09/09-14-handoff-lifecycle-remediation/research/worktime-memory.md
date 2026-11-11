# Worktime Memory

## 2026-09-14: Handoff Lifecycle Implementation

- The existing handoff Skill already owned immutable core/prompt assets,
  append-only per-handoff JSONL receipts, a per-handoff `flock`, target
  idempotence, cross-target rejection, retention archive, and the Trellis
  ownership bridge. The implementation extended those paths rather than adding
  a second ledger.
- Source readiness now means a sealed observed boundary plus a readable paired
  prompt. For a captured task, existing `ownership_quiesce` and
  `ownership_seal` receipt events are additionally required; target admission
  cannot bypass either source condition.
- Target intake uses the existing `not_admitted -> admitted -> reconciled`
  axis. `admitted` persists the direct target and a cumulative ordered prefix:
  `core_read`, `prompt_read`, `trellis_started`, `facts_reconciled`.
  `reconciled` is the sole final consumption marker. Progress cannot regress;
  a different target is refused after an attempt starts.
- A source workflow issue was verified during testing: rendering before source
  finalization was necessary to create the canonical prompt, but the renderer
  embedded mutable lifecycle status and therefore rejected the later idempotent
  render. The prompt no longer serializes lifecycle state; lifecycle status is
  only a render admission check. The source may render once to prepare the
  pair, finish source readiness, then render idempotently for delivery.
- Source commit `3c6160c9aee6eb4d9b7457525811f75d391b4757`
  (`fix(handoff): make intake recovery explicit`) was pushed to
  `origin/main`. The official installer first passed `--check`, then installed
  all 11 Skills from this checkout to `/home/penn/.codex/skills/pennix-skills`.
  The installed handoff `SKILL.md`, `handoff.py`, `workflow_contracts.py`, and
  `render_handoff_prompt.py` are byte-identical to the source checkout.
- Checks passed: 22 handoff/renderer tests, 10 installer tests, Python
  compilation, `git diff --check`, installer source validation and installed
  payload comparison. The installer deliberately omits source `tests/`; an
  attempt to discover tests in the installation returns an unimportable start
  directory and is not a runtime regression.
