# Implementation plan

1. Update the four owner guidance Skills listed in `design.md` with the sealed admission and
   transport boundaries.
2. Extend the existing offline contract tests in workflow-routing, FastCtx-routing, and
   decision-gates; Grok's launch contract is asserted from the FastCtx test.
3. Run the full discovered Python Skill test suite, parse the lifecycle catalog JSON, and run
   `git diff --check`; review scope and task artifacts.
4. Complete this task's source checks, then leave the final release for the sequential sibling
   lifecycle-governance task so both changes ship together.
5. After both tasks pass, bump `.trellis/.version` once from `0.6.25` to `0.6.26`, commit and push
   `main`, reinstall the complete Skills collection once through `$pennix-workflow-lifecycle`,
   and verify the installed collection against the published source and receipt. Stop on any
   owner failure.
