# Pennix workflow admission and owner-routing contracts

## Goal

Implement the already-sealed admission and owner-routing contract from root coordination task
`09-23-pennix-workflow-architecture-entry-state-convergence` in the owning `pennix-skills/main`
repository. This component task has no independent user decision frontier; the root task is the
source of cross-component requirements and release authorization.

## Scope and constraints

- Update the Pennix workflow routing, FastCtx routing, Grok retrieval, and decision-gates guidance
  so admission dimensions and native owner transport are explicit.
- Add offline static contract tests for admission classification, owner-first routing, prohibited
  FastCtx wrappers, owner-unavailable stopping, ordinary local FastCtx default, and post-hoc
  read-only analysis.
- Preserve each component's own state and execution channel. Do not add a runtime router,
  FastCtx interceptor, generic wrapper, second task/decision state machine, or external dependency.
- Do not edit Trellis beta, lifecycle state/receipts/staging, credentials, or user runtime assets.
- Target branch is `main`; update the canonical collection version only as part of release.

## Acceptance criteria

- [x] Admission dimensions distinguish work domain, evidence/change delivery, execution class,
      decision frontier, and implementation authorization; `analysis_only` and `subnode` are
      not substitutes for these classifications.
- [x] Workflow-native owner executables cannot be launched or advanced through FastCtx; an
      unavailable native channel remains blocked, while approved post-hoc ordinary result reads
      remain allowed.
- [x] Ordinary ownerless local file/CLI/build/test work remains FastCtx-default after owner
      preflight; no universal token-cost claim or runtime interception guarantee is introduced.
- [x] Static tests are offline, credential-free, and auto-discovered by the existing CI workflow.
- [x] Full Skill test suite (168 tests), lifecycle catalog JSON validation, and `git diff --check` pass.
- [ ] The source is committed and pushed on `main`, released using the existing version convention,
      then reinstalled and verified through the native lifecycle owner.
