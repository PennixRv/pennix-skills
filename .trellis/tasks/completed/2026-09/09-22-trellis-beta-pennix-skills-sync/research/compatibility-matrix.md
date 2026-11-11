# Trellis Beta Compatibility Matrix

Date: 2026-09-22

| Surface | Evidence checked | Disposition |
| --- | --- | --- |
| Lifecycle catalog | `skills/pennix-workflow-lifecycle/references/component-versions.json` | Update `trellis-cli` from `0.6.43` to verified `0.7.0-beta.7`. This is the only product version mismatch found. |
| Lifecycle adapter | `skills/pennix-workflow-lifecycle/scripts/lifecycle.py` and adapter modules | No change. It already reads the catalog target, validates npm candidates, and applies postconditions without a hard-coded Trellis version. |
| Lifecycle Skill | `skills/pennix-workflow-lifecycle/SKILL.md` | No change. It describes native Trellis ownership, project initialization separation, catalog authority, and no target-host source checkout. |
| Workflow routing | `skills/pennix-workflow-routing/SKILL.md` | No change. Trellis remains task/channel authority; FastCtx, OpenViking, CodeGraph and handoff are not conflated. |
| Decision gates | `skills/pennix-decision-gates/SKILL.md` | No change. Material ambiguity returns to planning; implementation does not open a new interactive gate. |
| Session handoff | `skills/pennix-session-handoff/SKILL.md` and scripts/tests | No change. Native task ownership, direct session identity, cumulative admission and pending-action stop are already represented. |
| Workflow doctor | `skills/workflow-doctor/SKILL.md` and `scripts/doctor.py` | No change. Diagnostic-only behavior does not repair or install workflow state. |
| Collection contract | Catalog collection entry and collection tests | No change. The collection remains installed by Codex `$skill-installer`; no local checkout or second installer is introduced. |
| Retired protocols | Product-source-only search excluding `.trellis` history and the Windsurf CI phrase “source checkout” | No actionable retired `parallel-work`, `evidence-report`, `review-gate`, terminal JSON transport, or target-host source-checkout entry point remains. Historical task records are retained as evidence. |
| Release metadata | `.github/workflows/verify.yml`, tags and recent history | Verification runs on push/PR; no existing npm/package release contract or tags were found for this Skills collection. Push `main` is required; no speculative package release is added. |

## Verification commands

- `npm view @pennixrv/trellis@0.7.0-beta.7 version --json` -> `0.7.0-beta.7`
- `npm view @pennixrv/trellis-core@0.7.0-beta.7 version --json` -> `0.7.0-beta.7`
- `npm view @pennixrv/trellis@0.7.0-beta.7 dist.tarball --json` -> a registry tarball URL
- Product-source `rg` found no remaining `0.6.43`; the only source hits for “source checkout” are the normal Windsurf release CI check and test.

## Delivery

- Commit: `9ecb96b37671b5e700900a02e6de4a756188037a`.
- Push: `origin/main` resolves to the same commit.
- Release/install: this collection has no package release contract or tags; the reproducible delivery path remains Codex `$skill-installer` resolving `PennixRv/pennix-skills` `main`.
- Verification: shell syntax, Python compilation, all repository test files, and `git diff --check` passed before push.
