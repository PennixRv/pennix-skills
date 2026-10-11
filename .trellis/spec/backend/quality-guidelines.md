# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

<!--
Document your project's quality standards here.

Questions to answer:
- What patterns are forbidden?
- What linting rules do you enforce?
- What are your testing requirements?
- What code review standards apply?
-->

(To be filled by the team)

---

## Forbidden Patterns

<!-- Patterns that should never be used and why -->

(To be filled by the team)

---

## Lifecycle Verification Contract

- `verify --component <key>` validates only the selected catalog component and
  fails closed for an unknown key. It must not evaluate unrelated components,
  static assets, or configuration targets.
- Full `verify` checks every catalog component and the core/enabled
  configuration targets. Its result distinguishes `scope`, `failures`, and
  `advisories`; only failures make the status `blocked`.
- A readable installed version below a readable `repository-latest` candidate
  is `upgrade-available` and is advisory. Missing, unknown, unsafe-owner,
  pinned-drift, static/collection integrity failure, upstream failure, and
  required configuration readiness failure remain blocking.
- For AUR packages, compare the CLI-reported version with the repository
  version without the trailing Arch `pkgrel` (for example, `0.156.1-1` versus
  `0.156.1`), while retaining the complete candidate version in inventory.
- Tests must cover scoped isolation, unknown selectors, repository candidate
  advisories, candidate-unavailable blocking, pinned drift, and full
  configuration checks.

---

## Session Handoff Intake Contract

- Current handoff schema stores conversation history once under `conversation`;
  `source.rollout` contains capture identity and boundary only, while timeline
  entries reference candidate event indices instead of copying message text.
- Validate every consumed field and cross-reference before rendering, reading,
  lifecycle changes, ownership operations, or retention. Integer fields reject
  booleans, and malformed packages fail through the controlled contract error.
- Core and history views are read-only, deterministically serialized UTF-8 text
  with Unicode-character offsets. Read ranges do not mutate the package or
  create persistent cursors. Admission records actual history ranges in its
  existing receipt; structural validation does not claim semantic reading.
- Historical schemas remain inspectable but read-only. Do not migrate them or
  accept their previous admission semantics under the current schema.
- Tests cover malformed consumed shapes at shared entry points, lossless paging
  of long Unicode text, receipt range boundaries, and historical write gates.

---

## Required Patterns

### Skill collection deployment boundary

- The repository checkout is the source of truth. The installed collection is
  a replaceable delivery copy and must not become an edit location.
- `pennix-skills-install` defaults to
  `${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills`, but callers may pass an
  explicit `--dest` ending in `skills/pennix-skills` for a host-selected
  discovery root. `PENNIX_SKILLS_ROOT` is a caller convention for reusing that
  selected collection root in direct Skill commands; the installer does not
  scan for roots or persist host-wide discovery state.
- Changes to this boundary require tests for the unchanged default, an
  explicit host-selected root, invalid destinations, and atomic replacement.

### Collection commands and configuration owners

- Schema 2 receipts bind the tree digest and the finite catalog command map.
  Explicit `replace-staged` may migrate a verified schema 1 tree; it may not
  overwrite an invalid or drifted receipt. Collection, receipt and newly
  created command links roll back together on replacement failure.
- A user command link must be absent or match the existing receipt and exact
  collection target. Unowned paths and other `CODEX_HOME` targets are conflicts;
  PATH shadowing is reported independently of the link's state.
- Windsurf readiness and configuration resolve its native executable from the
  receipted collection. They never select an arbitrary same-name PATH command.
- SiYuan owned helper commands may use a different absolute interpreter path
  only when filesystem samefile proves the expected executable and the two-item
  argv keeps the exact installed helper path. Other fields and owned stanza
  bytes remain strict; readiness never rewrites configuration or credentials.
  Unverifiable paths, changed scripts or interpreters, and extra argv fail closed.
- Retired configuration migration uses explicit `reconcile`, validates private
  files and known record shapes before writing, preserves other credentials
  and target selections, verifies writes and reports partial failures closed.

### Profile digest reconciliation

1. **Scope / trigger:** A configuration catalog change may leave a valid current
   namespace profile stale. Only explicit workflow-state reconciliation refreshes
   it; component installation and readiness probes do not configure credentials.
2. **Signature:** `python3 skills/pennix-component-lifecycle/scripts/lifecycle.py
   reconcile --component pennix-workflow-state --yes` retains the existing CLI.
3. **Contract:** The private profile has exactly `schema: 1` (integer, not bool),
   a lowercase 64-hex `catalog_digest`, and a unique string `targets` array.
   Namespace directories are owned and mode 0700; the profile is owned, regular,
   mode 0600, and has no symlink ancestor. Every selected ID belongs to the current
   catalog. Only default-enabled and selected targets are probed, using the same
   local adapter calls as discovery. All must be `ready` or `configured`.
   A refresh changes only the digest value, preserving target order and selection.
4. **Validation / errors:** Safe stale profiles return `refreshed`; current ones
   return `already-match` without rewriting. Invalid shapes, unknown targets,
   unsafe paths/modes, and readiness failures return `blocked` without a write.
   Compare the original bytes before atomic replacement, verify written bytes,
   and roll back only while the destination still equals this attempt's output.
   Preserve concurrent external bytes and report `blocked` with
   `rollback-incomplete` when restoration cannot safely complete.
5. **Cases:** Good: a renamed catalog member with unchanged target IDs and ready
   adapters. Base: a current profile needs no write. Bad: a removed target ID or
   an unready core provider cannot be approved merely by replacing its digest.
6. **Tests:** `test_lifecycle.py` asserts ordered targets, default/selected probe
   coverage, no configure/prompt, idempotence, invalid/private-path rejection,
   pre-replacement comparison, write/readback failures and external-byte survival.
7. **Wrong / correct:** Do not re-run configure to refresh a digest or overwrite
   third-party bytes during rollback. Use explicit validated reconcile and keep
   full host verify separate from profile reconciliation.

---

## Testing Requirements

<!-- What level of testing is expected -->

(To be filled by the team)

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
