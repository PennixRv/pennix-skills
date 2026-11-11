# Hindsight lifecycle integration design

## Ownership and upstream boundary

Target `pennix-skills` `main`. Install exactly `@vectorize-io/hindsight-coding-agents@0.6.1`. At this release the official Codex path is `hindsight-coding-agents install codex`: three hooks in `~/.codex/hooks.json`, `[features] hooks = true` when absent, and `[mcp_servers.hindsight]` in `config.toml`. It is an npm integration, not a Codex native plugin. The upstream installer anchors these files and its staged runtime at Node `homedir()` (`~/.codex`, `~/.hindsight/coding-agents`, `~/.agents/skills`); it does not honor a non-default `CODEX_HOME`. Pennix invokes the owner only when effective `CODEX_HOME` is unset or exactly `$HOME/.codex`, and fails closed otherwise. Reuse upstream install/uninstall ownership and its marker-based idempotence; Pennix owns selecting/pinning the single supported harness, static project policy, secret readiness and redacted lifecycle verification. Do not clone the upstream installer, wrap it by changing `HOME`, or manually synthesize its hook files.

## Configuration and secret boundary

Use the upstream native `~/.hindsight/coding-agent.json` schema. Pennix's static policy materialization writes only non-secret fields and preserves all user-owned keys, in particular an existing `apiToken`. The explicit secret configure action prompts on `/dev/tty` without echo and atomically merges only `apiToken`; file and parent directory are owner-only (`0600`/`0700`). Hindsight v0.10.1 also accepts `HINDSIGHT_API_TOKEN`, but this workflow does not add a shell wrapper or second secret distribution framework; the official config file is the canonical client configuration boundary. Verify reports only configured/missing/blocked, never values.

Use `serverMode=self-hosted`, task-provided API URL, `optInOnly=true`, `autoReflect=true`, `autoUpdate=false`, `autoSeed=false`, `codebaseSurvey=false`, and `gitIngest=none`. `autoReflect` is the supported v0.6.1 first-prompt, one-time recall: Codex caps the reflect request at 20 seconds and uses the package's low reflect budget; when eligible reflect failures occur, the package falls back to up to three knowledge-page results, then up to 2,000 recall tokens. Its injected preamble attributes the material to Hindsight memory and marks it historical/heuristic. There is no `autoInject` field. Keep upstream Stop write-back enabled as selected. Static update must preserve the API token and unrelated native config; uninstall removes only fields/registrations that Pennix owns and must refuse ambiguous ownership. Evidence is recorded in `research/coding-agents-0.6.1-contract.md`.

## Stable project bank registration

Project memory is opt-in only. The explicit registration operation accepts one existing Trellis project root, resolves it to a canonical path, and stores a stable opaque ID under `.trellis/config.yaml`:

```yaml
pennix:
  memory:
    bank_id: pennix-project-<stable-id>
```

Trellis' bundled config parser accepts nested unknown mappings; its current native `config.yaml` parser is the project asset owner. Pennix must make the smallest targeted edit, preserve other settings/comments, refuse symlinked/ambiguous config and conflicting ownership, then add exactly the current absolute path → bank ID entry in upstream `mapPathToBank`. On a new machine or moved checkout, explicit registration reads the existing ID and updates only the path mapping. Never generate identity from basename, share project banks, or auto-opt-in all repositories. Deregistration removes the selected path mapping only; deletion/reset of the project ID is not implicit.

## Verify and failure semantics

`verify` is read-only and redacted. It checks exact installed npm version, Codex hook/MCP ownership markers, the native `[features] hooks = true` setting, selected settings, private config mode/token readiness, registered path mappings and no competing memory-owner entry. Missing optional project registration is not an install failure; a registered project's mapping mismatch is blocked. Never report “ready” based only on package presence. Unknown keys, malformed config, external modifications or unsupported upstream schema block edits instead of being overwritten.

## Test boundary

Unit tests use isolated HOME with `CODEX_HOME` unset or set to `$HOME/.codex`, plus fake upstream command execution. Test native installer invocation and reruns, custom `CODEX_HOME` fail-closed behavior, preserving unrelated Codex config, hidden secret prompt/permissions/redaction, static update preserving token, project ID creation/read/remap/unregister, symlink and malformed YAML rejection, opt-in routing, and read-only verify. Run them only in the parent task's unified post-implementation test phase after every owner has finished implementation.
