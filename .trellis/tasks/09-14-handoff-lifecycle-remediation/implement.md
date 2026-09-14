# Implementation Plan

1. [x] Trace current source readiness, receipt replay, admission, retention,
   ownership bridge, renderer and focused tests.
2. [x] Add the explicit core-read attestation step and ordered prefix decoder.
   Reuse the existing target axis and per-handoff lock.
3. [x] Require the paired prompt during `finalize`; make partial intake write
   `admitted`, advance only for the same target, and write `reconciled` only
   for the complete prefix.
4. [x] Make a completed retention archive retry idempotent without changing
   admission or task state. Update user-facing Skill wording and short prompt.
5. [x] Add focused regressions for missing pair, partial/recovery/cross-target,
   post-consume compaction re-entry, and archive retry. Run the source suite
   and inspect the diff.
6. [ ] Publish/install through the existing mechanism, then record source and
   root-side receipts.

## Validation

- `python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py'`
- Applicable static Skill/install checks from the existing release workflow.
- A temporary isolated Trellis fixture exercising prepare, render, finalize,
  partial admit, final admit and archive retry.

## Rollback

Revert the scoped Pennix Skills source commit and reinstall the prior published
revision. Do not edit `/home/penn/.codex` as a source-level rollback.
