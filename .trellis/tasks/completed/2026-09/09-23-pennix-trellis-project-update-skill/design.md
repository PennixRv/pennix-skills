# Design: Trellis Project Update Skill

## Owner boundary

`pennix-trellis-project-update` is the owner for an already initialized project's Trellis asset maintenance. It delegates all file generation and conflict classification to the current native `trellis` CLI. It does not own system package installation, the Skills collection, read-only diagnosis, task semantics, Channel lifecycle, or the Trellis source repository.

## Update protocol

1. Require an explicit project root and load its `AGENTS.md`, `.trellis/workflow.md`, `.trellis/config.yaml`, `.trellis/.version`, and `.trellis/.template-hashes.json` when present.
2. Run `trellis --version`, `trellis platforms`, and `trellis update --dry-run` from that root.
3. Use `trellis update --create-new` for a safe non-interactive update. It updates native files that are safe to update and creates `.new` candidates for modified template files. Use `--skip-all` only when the task explicitly chooses preservation without candidates. Use `--migrate` or `--force` only for named, reviewed decisions.
4. Refresh a workflow separately with `trellis workflow`. Require a template id and an immutable source/ref for Marketplace content. Begin with `--create-new`; apply only a reviewed candidate. Never infer the source or replace the active workflow because a newer template exists.
5. Re-run dry-run and project checks; inspect the diff and reject runtime, secret, cache, task, workspace, and unrelated user-file changes.

## Pennix compatibility

When the selected template is the current Pennix `codex-subnode-channel`, the Skill checks that the refreshed content still expresses inline main-session delivery, explicit independent evidence, durable artifacts, coordinator acceptance, and unit-sized evidence. It does not turn normal implementation into a subnode dispatch and does not replace the project workflow with a native template.

## Stop conditions

Stop and route to the decision-gate path when `.trellis` is absent, the workflow source/ref/template is not explicit, a migration or overwrite would be needed but is not sealed, or the native command/verification fails. Do not create a second updater, manually edit template hashes, copy files from a Trellis checkout, or use FastCtx to simulate Trellis ownership/lifecycle.
