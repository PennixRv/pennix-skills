# Technical Design

## Change Boundary

Only the independent `pennix-skills` repository is mutable. The smallest confirmed behavior gap is the stale lifecycle catalog target and its test expectation. The behavior lives in `skills/pennix-workflow-lifecycle/references/component-versions.json`; the test mirror lives in `tests/test_lifecycle.py`.

## Data Flow

`component-versions.json` -> `lifecycle.py::load_catalog` / `component_target_version` -> discovery and package candidate checks -> lifecycle postconditions. Tests load the same catalog and assert observable contract values.

The version is not copied into a Skill prose document or adapter. Root integration docs may record the accepted external commit as evidence, but they are not a component version source.

## Compatibility Review

Review these paths before editing:

- catalog schema and Trellis package metadata;
- lifecycle version normalization, candidate lookup and postcondition checks;
- lifecycle tests and collection tests;
- lifecycle/routing/decision-gates/handoff/doctor product text;
- README and release metadata.

Treat `.trellis/tasks/` and `.trellis/workspace/` history as evidence only. Do not rewrite historical task records to make a product search look clean.

## Rollout And Rollback

Run all checks before commit. If package metadata or tests disprove the target, revert only this task's edits and record the blocker. Do not change package ownership or install anything on the host as part of this task.
