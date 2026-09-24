# Pennix workflow lifecycle state and asset governance

## Goal

Move lifecycle-owned state to the XDG namespace, add explicit legacy reconciliation, distinguish static and credential state, and report unreceipted staging without mutating it.

## Requirements

- Lifecycle-owned profile and static receipts must live below an XDG state namespace, isolated by the normalized resolved `CODEX_HOME` digest. No new final state may be created below `CODEX_HOME`.
- Live Skills collection receipts remain next to the live collection. Native installer temporary directories remain installer-owned and are not lifecycle state.
- Static asset state and credential/configuration state remain separate in the catalog and lifecycle contracts.
- Existing legacy lifecycle records may be migrated only by an explicit `reconcile --component pennix-workflow-state --yes` action. The action must be read-only until all destinations are validated, atomic per file, conflict-safe, and recoverable on failure.
- Direct-child `.pennix-skills-stage*` candidates under the Skills destination are reported as redacted `unknown` advisory observations. Discovery, verify, and reconcile must not infer provenance, delete them, or treat them as lifecycle-owned state.
- The lifecycle must expose a single state component with `reconcile` as its only managed action; install, configure, upgrade, uninstall, and verify remain not applicable for that component.

## Acceptance Criteria

- [ ] Profile and tmux receipt writes use the XDG/hash namespace with private directory/file permissions.
- [ ] Catalog validation accepts the state component and rejects invalid state action contracts.
- [ ] Discover and verify report staging candidates without mutation; staging observations do not block lifecycle-owned verification.
- [ ] Reconcile migrates only the exact allow-listed legacy records, preserves legacy state on conflicts or failures, and removes old files only after post-write verification.
- [ ] Tests cover namespace isolation, staging advisory behavior, successful migration, conflict retention, and invalid/unsafe records.
- [ ] Source checks, release, reinstall, and final lifecycle verification are recorded by the root coordination task.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
