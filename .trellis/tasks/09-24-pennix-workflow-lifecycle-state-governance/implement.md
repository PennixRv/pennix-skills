# Implementation Plan

1. Add the state component contract and explicit `reconcile` dispatch.
2. Complete XDG/hash state inspection, exact legacy allow-list migration, atomic write/verify, and failure retention.
3. Add read-only staging candidate reporting and keep it advisory for lifecycle-owned verification.
4. Update lifecycle documentation and contract tests.
5. Run the full test suite, update the component version once, commit and push `main`, reinstall through the native lifecycle flow, and record the final evidence in the root task.

## Completion lock

The task is complete only when the source tests pass, the released `pennix-skills` commit is installed into the Codex environment, lifecycle discover/verify results are captured, and no unapproved cleanup or credential migration has occurred.
