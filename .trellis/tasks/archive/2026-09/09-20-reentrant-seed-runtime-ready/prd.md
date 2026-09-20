# 重构可重入远程 Seed 为完整工作流入口

## Goal

将 Arch 远程 seed 改为可重入的 Pennix 运行时准备入口：第一个新 Codex 会话只安装 lifecycle bootstrap，第二个新会话由该 bootstrap 完成 collection 并部署工作流，无需持久 source checkout。

## Background

- `seed-arch.sh` currently rejects any pre-existing `CODEX_HOME/config.toml` or
  `auth.json`, so a successful seed cannot be safely re-run.
- The previously released single-Skill flow then requires a clean local source
  checkout. That is a development workflow, not a target host deployment
  contract.
- Codex's system `$skill-installer` installs public GitHub Skill paths through
  temporary downloads and does not keep a source checkout. It accepts multiple
  paths and a destination root, but is available only inside a Codex agent
  turn; it is not an `openai-codex-bin` shell command.
- `skills/grok-search` and `skills/windsurf-code-search` are submodules, so
  installation must use their own public repositories rather than assume that
  the parent repository archive contains their content.

## Requirements

- R1: Remote and local seed runs must be reentrant. Existing `config.toml` and
  `auth.json` are preserved exactly; a missing counterpart is created by
  prompting only for the missing value. Re-entry must not expose a secret.
- R2: Seed retains its Arch/WSL2, official `npm`, AUR Codex, and static
  seed-template scope. It
  must not install an isolated bridge, create a local `pennix-skills` checkout,
  or introduce a custom bundle/distribution installer.
- R3: Seed completion output contains two unambiguous new-session prompts. The
  first uses `$skill-installer` only for `pennix-workflow-lifecycle` at the
  managed destination, then ends; it contains no complete-collection child
  Skill list or source-checkout instruction.
- R4: The second-session lifecycle bootstrap must use the catalog's internal
  contract to route the remaining seven direct Skills and two submodule Skills
  to their owning public repositories under one
  `CODEX_HOME/skills/pennix-skills` collection.
- R5: The second Codex session invokes `$pennix-workflow-lifecycle` directly.
  It recognizes the exact `bootstrap` collection state, completes it without a
  third session, then continues deployment. Documentation must call this a
  two-session discovery boundary, not two deployment stages.
- R6: Lifecycle discovery and verification for `pennix-skills` must recognize
  the managed installed collection without a target-host source checkout.
  Lifecycle must not claim checkout-backed install or upgrade support that is
  unavailable on the target host.
- R7: README, Skill instructions, catalog metadata, tests, and seed output
  describe the same ownership and lifecycle boundary.

## Acceptance Criteria

- [x] A fresh seed produces protected `config.toml` and `auth.json`, emits the
  lifecycle-bootstrap `$skill-installer` request and second-session lifecycle
  prompt, and never emits a complete-collection child Skill list or
  source-checkout instruction.
- [x] Re-running seed with both existing files succeeds without prompts or file
  changes; with one missing file it prompts only for that file's required value.
- [x] The catalog names all ten current Skills and routes the remaining nine
  Skills to their owning public repositories under one destination; the user
  only receives the lifecycle-bootstrap prompt.
- [x] `pennix-skills` lifecycle `discover` and `verify` operate from the
  installed collection without `--source`; unavailable install/upgrade actions
  are reported as native-owner rather than falsely accepting a checkout path.
- [x] Seed, lifecycle, and collection tests pass, including the re-entry,
  bootstrap-state, and collection-inventory cases; the full local workflow
  integration check passes.
- [x] User-facing documentation contains no remaining bridge or target-host
  source-checkout deployment path.

## Out Of Scope

- Installing a custom runtime bundle, creating a new release artifact, or
  implementing a non-native replacement for `$skill-installer`.
- Project initialization, component package installation beyond the current
  seed-owned Codex package, and a seed uninstall mode.
- Overwriting, deleting, or rotating existing credentials.

## Verification

- `bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh`
- `find skills -path '*/tests/test_*.py' -type f -print0 | sort -z | xargs -0 -n1 python3`
- `git diff --check`

All checks passed on 2026-09-20. The generic source specs contain no lifecycle
operation contract to update; the durable behavior is recorded in this PRD,
the catalog, Seed output, and lifecycle Skill.
