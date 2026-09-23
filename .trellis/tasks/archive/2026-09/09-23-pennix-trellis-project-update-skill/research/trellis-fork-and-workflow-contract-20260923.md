# Trellis Fork and Workflow Contract

## Verified revisions

- Local Trellis fork: branch `pennix/v0.7-beta`, `HEAD` and `origin/pennix/v0.7-beta` both resolve to `717bd21b4fdd08e59218231db9afbceba75ff5dd`; CLI reports `0.7.0-beta.10`.
- Local Trellis Marketplace: branch `pennix/v0.7-beta`, `HEAD` and `origin/pennix/v0.7-beta` both resolve to `75842e6cd56237e48d8899bec7036397cb7967ee`.
- Evidence paths: `Trellis/packages/cli/src/commands/update.ts`, `Trellis/packages/cli/src/commands/workflow.ts`, `Trellis/packages/cli/src/templates/common/bundled-skills/trellis-meta/references/local-architecture/generated-files.md`, and `Trellis/marketplace/workflows/codex-subnode-channel/workflow.md`.

## Native behavior that the Skill must follow

- `trellis update` supports `--dry-run`, `--force`, `--skip-all`, `--create-new`, `--allow-downgrade`, and `--migrate`.
- Dry-run makes no changes. `--create-new` writes `.new` copies for modified template files and leaves the current file in place. `--skip-all` preserves modified files. `--force` overwrites changed files and is therefore not a safe default.
- Update creates a native backup and updates version/hash metadata only for files actually written. User data under tasks, workspace, specs, runtime, caches, and credentials is not a generic replacement target.
- `trellis workflow` is a separate selection path. `--list` discovers templates; `--marketplace` accepts a source; `--create-new` writes `.trellis/workflow.md.new` without touching the active file or hash; non-native workflow content is treated as user-managed and does not silently become native during update.
- The current project workflow file is the local semantic source of truth. Trellis does not provide enough provenance to infer a remote marketplace source/ref from arbitrary workflow bytes, so a refresh must require an explicit source/ref/template decision.

## Latest Pennix workflow contract

The beta `codex-subnode-channel` template requires the main session to deliver by default; a subnode is only for explicit independent evidence; brief, worklog, and report artifacts are durable; report status is not acceptance; the coordinator validates and records acceptance; and read-heavy evidence is split into units that persist conclusions before the next unit. The update Skill must preserve these semantics when refreshing that template.

## Closed decisions

1. Project update remains a Skill, not a new lifecycle adapter: the native Trellis CLI owns project files.
2. The safe default is dry-run followed by native update with `.new` conflict copies; overwrite and migration require a sealed task decision.
3. Non-native workflow refresh requires an explicit immutable source/ref/template; no source or workflow switch is inferred.
4. Installation remains the existing complete collection staging/replacement path; no checkout is created on the target host.
