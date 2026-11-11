# Implementation plan

1. Bind this component task, curate the existing lifecycle/configuration/routing
   specs and this task artifacts, then run native validation before start.
2. Update the catalog and materialized source snapshots from the already
   published Grok v0.3.0 and verified Windsurf 0.1.16 artifacts. Remove the
   Firecrawl target and update lifecycle instructions.
3. Extend collection receipt and command-link transaction code with schema 2,
   exact target validation, PATH shadow detection, schema 1 explicit migration,
   rollback and uninstall safeguards. Add focused fixtures for normal,
   duplicate, drifted, unsafe and rollback cases.
4. Implement the finite state reconcile changes for retired Firecrawl fields,
   profile target and cooldown evidence; update Windsurf's shared collection
   resolver and add no-global-command/unsafe-entry fixtures.
5. Add the approved routing Skill contract text and tests. Run the lifecycle,
   configuration, install and routing test suites plus `git diff --check`.
6. Commit and push `main`, then hand the exact commit to the parent task for
   native staging/install. Do not edit the installed `/home/penn/.codex`
   collection directly.

## Rollback

Before commit, revert only this task's source diff. During lifecycle execution,
use the existing atomic receipt/collection transaction and native owner
reconcile; never restore a whole user configuration directory.
