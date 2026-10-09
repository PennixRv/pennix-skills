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
- Retired configuration migration uses explicit `reconcile`, validates private
  files and known record shapes before writing, preserves other credentials
  and target selections, verifies writes and reports partial failures closed.

---

## Testing Requirements

<!-- What level of testing is expected -->

(To be filled by the team)

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
