---
name: pennix-trellis-project-update
description: "Safely update an existing Trellis-managed project's generated assets and explicitly selected workflow through the current native Trellis CLI. Use when the user asks to update or upgrade project Trellis assets or its workflow; do not use for system component deployment or read-only diagnosis."
---

# Pennix Trellis Project Update

Use this Skill for an existing project that already has Trellis initialized.
The project root must be explicit. The native `trellis` CLI remains the only
owner of project asset generation and conflict classification.

## Ownership

- Use `$pennix-workflow-lifecycle` for global component installation,
  configuration, collection replacement, or verification.
- Use `workflow-doctor` for a read-only local diagnosis.
- Use this Skill for an existing project's Trellis update and selected workflow
  refresh. Do not copy files from a Trellis checkout or create a second updater.
- Trellis task, Channel, handoff, Hook, and platform-native protocols retain
  their native owners. Do not simulate them with a script or a FastCtx state
  machine.

## Preflight

From the explicit project root:

1. Read the closest `AGENTS.md`, `.trellis/workflow.md`, `.trellis/config.yaml`,
   `.trellis/.version`, `.trellis/.template-hashes.json`, and
   `.trellis/workflow-provenance.json` when present.
2. Confirm that `.trellis/` exists. If it does not, stop and use the native
   Trellis initialization flow; this Skill never initializes a project as an
   update side effect.
3. Run `trellis --version`, `trellis platforms`, and:

   ```bash
   trellis update --dry-run
   ```

4. Record the project workflow currently selected, its task/repository owner,
   and the exact update scope in the active Trellis task. If the request
   changes a workflow source, template, migration, or overwrite policy, use
   `$pennix-decision-gates` before implementation and persist the decision.

## Trellis asset update

Use the native update command. The reentrant non-destructive path is:

```bash
trellis update --create-new
```

This lets the current fork update safe and new template files while writing
`.new` candidates for modified template files. Review each candidate against
the project contract before applying it. `--skip-all` is allowed when the
sealed task explicitly chooses to preserve every modified file without
candidate copies:

```bash
trellis update --skip-all
```

Do not use `--force` as the default. Use it only for the exact files and
decision named in the active task. Use `--migrate` only when the task
acceptance explicitly includes the native migration, because migrations may
rename or delete deprecated files. Never hand-edit
`.trellis/.template-hashes.json` to make a conflict disappear.

Treat these as project-owned or runtime-owned and preserve them during a
generic update: `.trellis/spec/`, `.trellis/tasks/`, `.trellis/workspace/`,
`.trellis/.runtime/`, credentials, caches, logs, databases, and unrelated user
files. Let native Trellis decide which managed platform files and root managed
blocks are safe to refresh.

## Workflow refresh

Workflow selection is separate from `trellis update`. First discover the
available templates:

```bash
trellis workflow --list
```

For Marketplace content, require all three values before fetching or writing:
the template id, an explicit source, and an immutable ref (normally a commit
SHA) in that source. A branch name or the current file bytes is not sufficient
provenance. Then preview the candidate without replacing the active workflow:

```bash
trellis workflow --list --marketplace 'gh:OWNER/REPO/path#IMMUTABLE_REF'
trellis workflow --template TEMPLATE_ID \
  --marketplace 'gh:OWNER/REPO/path#IMMUTABLE_REF' \
  --create-new
```

`--create-new` writes `.trellis/workflow.md.new` only; it does not update the
active workflow or provenance. Review the entire candidate against the current
project rules and active task, record acceptance, then apply that same explicit
template/source/ref. Use `--force` only when the reviewed active file is
classified as modified and the task explicitly authorizes that replacement.
After applying, run:

```bash
trellis workflow --verify
```

This verifies the recorded workflow id, source/ref, content hash, and active
bytes. A missing provenance record is not repaired by matching file bytes:
select the exact source/ref and materialize it through the native command, or
record the legacy state as unverifiable and stop before replacement. Do not
silently switch between `native`, a Marketplace template, or a saved local
variant.

For a `trellis update --create-new` candidate, decide each exact `.new` path
before cleanup. Keep every pending or non-identical candidate. Remove a
byte-identical sidecar only after the active file has been accepted and the
project/task records that disposition; compare that one explicit path, not a
directory-wide glob:

```bash
test -f PATH.new && test ! -L PATH.new && cmp -s -- PATH PATH.new && rm -- PATH.new
```

Delete a non-identical sidecar only when its exact rejection is explicitly
recorded and authorized. Never use broad `find ... -delete`, recursive cleanup,
or an unreviewed command to remove `.new` files.

The current Pennix `codex-subnode-channel` workflow keeps inline main-session delivery
as the default; subnodes are only for explicitly requested independent evidence,
and their durable reports still require coordinator validation and
acceptance.

## Completion check

After resolving every intended candidate:

1. Re-run `trellis update --dry-run`; when a workflow changed, run
   `trellis workflow --verify` against its persisted immutable provenance.
2. Run `git diff --check` and the project's relevant tests, lint, or type checks.
3. Inspect `git status` and the full diff. Only the requested project assets and
   durable task evidence may remain changed; every `.new` candidate must be
   accepted, explicitly rejected, or retained as an explained pending item.
4. Confirm `.trellis/.version` and native template hashes were changed only by
   Trellis, and that no secret, session, cache, runtime state, or source
   checkout entered the project diff.

If the native command fails, provenance is missing, a modified file needs an
unsealed overwrite decision, or validation is incomplete, stop and return to
the planning/decision-gate path. Do not guess, force, or report completion.
