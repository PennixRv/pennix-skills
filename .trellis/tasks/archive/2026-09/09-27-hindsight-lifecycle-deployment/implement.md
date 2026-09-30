# Implementation order

1. Run `trellis-before-dev` for the lifecycle backend/source layer. Re-read its exact specs, the existing lifecycle catalog/adapters/configuration tests, current user-level asset ownership, and v0.10.1 installer/config source before touching code.
2. Update the lifecycle catalog for the exact package pin and upstream Codex install/uninstall ownership; remove the OpenViking plugin/configuration target from active managed inventory without deleting its user installation yet.
3. Add only the Hindsight configuration target/adapter needed for the selected official package: preflight the upstream `HOME/.codex` limitation and owner collisions before invoking it; static defaults separate from interactive API-token input, private native config merge, redacted readiness, idempotent update/uninstall. Preserve unrelated Codex/Hindsight configuration and refuse unknown ownership.
4. Add explicit project register/remap/unregister using `.trellis/config.yaml:pennix.memory.bank_id` plus the native Hindsight `mapPathToBank` path map. Preserve source formatting and unrelated project configuration; no implicit current-directory enrollment.
5. Update `pennix-workflow-lifecycle/SKILL.md` and any lifecycle docs/verify schema to document the one Hindsight component, official npm integration, explicit project enrollment and separate static/secret actions. Do not place project-specific rules in the root coordinator.
6. Finish all implementation across this task and its sibling tasks before running tests. Then participate in the parent's single unified test phase: lifecycle test suite, integration tests under temporary HOME with default/equivalent `CODEX_HOME`, and full verification matrix. Fix failures, then rerun the affected tests and full cross-boundary checks.
7. Commit and push only Pennix `main` after full checks. Publish a new package/skill release only if the repository's current version/release contract requires it; reinstall Pennix Skills and run redacted global verify. Never include the API token in Git or test output.

## Stop conditions

- The locked upstream package version or native config schema differs from the recorded contract.
- `CODEX_HOME` is custom and differs from `$HOME/.codex`, or the native installer would collide with user-owned files.
- Upstream install/uninstall would overwrite unrelated user-owned Codex hooks/MCP/Skills, or cannot be scoped to Codex only.
- Stable project identity cannot be represented safely in the project Trellis config, or `mapPathToBank` cannot enforce the selected opt-in boundary.
- Secret/config ownership is ambiguous or permissions cannot be maintained.

Return exact evidence to the parent planning gate on a stop; do not silently switch to a wrapper, shell-wide environment export, all-project opt-in, different package version, or other integration.
