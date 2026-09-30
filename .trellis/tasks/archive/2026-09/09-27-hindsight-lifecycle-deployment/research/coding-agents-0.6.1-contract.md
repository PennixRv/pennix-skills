# `hindsight-coding-agents` 0.6.1 lifecycle contract

## Source identity

- npm package: `@vectorize-io/hindsight-coding-agents@0.6.1`
- Published repository path: `hindsight-integrations/coding-agents`
- Inspected package files: `README.md`, `dist/installer.js`, `dist/claude-hook.js`, `package.json`
- Package artifact integrity recorded during retrieval: `sha512-7CdHjyRsvkWqK6k2aa4QifGh3iJfdYL7o2jW+JzgKltI/QKka0XI1YJt3zX6e0b+HXO5ll2/c3+3DVhD8N6BSA==`
- No API token or other secret was read or recorded.

## Verified facts

1. The native configuration file is `~/.hindsight/coding-agent.json`; `HINDSIGHT_CONFIG` can relocate it. The package reads `autoReflect`, `autoSeed`, `codebaseSurvey`, `autoUpdate`, `gitIngest`, `retainSessions`, and `mapPathToBank`. `autoInject` does not appear in this release's documented or resolved configuration.
2. Codex install is `hindsight-coding-agents install codex`. The installer writes Codex hooks to `$HOME/.codex/hooks.json`, the `hindsight` MCP section and hooks feature setting to `$HOME/.codex/config.toml`, and the companion Skill under `$HOME/.agents/skills/hindsight-coding-agent`.
3. The package stages its runtime at `$HOME/.hindsight/coding-agents`. It does not consult `CODEX_HOME`; pointing Codex elsewhere would leave Codex reading a different hook/config directory. Pennix must reject a non-default `CODEX_HOME` before any owner command rather than add a wrapper or claim readiness.
4. The installer merges Codex hook entries, rewrites JSON formatting, appends/replaces its TOML MCP block, leaves `hooks=true` on uninstall, and creates `<file>.hindsight-backup` copies for files it edits. Its marker filtering matches any serialized hook containing the broad string `coding-agents`; its TOML removal targets the named `[mcp_servers.hindsight]` block. Therefore Pennix must preflight conflicting owner entries and preserve unrelated configuration semantically, not promise byte-for-byte preservation.
5. First-prompt recall uses `autoReflect=true` by default. The Codex hook uses a low reflect budget and 20-second cap, runs reflect once on the first prompt, and injects a Hindsight-attributed historical-memory preamble. On eligible reflect errors it searches at most three knowledge pages, then attempts observation recall with `maxTokens=2000` within a 7-second fallback budget. `autoReflect=false` disables this injection and instead tells the agent to search knowledge pages first, so it does not meet the selected automatic first-session recall contract.
6. Defaults for `autoSeed`, `codebaseSurvey`, and `autoUpdate` are `true`, and `gitIngest` defaults to `message`; Pennix must explicitly disable those paths to honor the empty-bank/no-broad-ingest/version-pin contract. `retainSessions=true` is the native Stop write-back behavior selected by the parent task.

## Evidence locators

- `README.md:423-444, 466-493, 508-543`: config path/layers, opt-in routing, recognized fields and defaults.
- `dist/installer.js:4488-4546, 4646-4680`: Codex paths, native install/uninstall behavior and runtime staging.
- `dist/installer.js:4177-4205, 4224-4294`: marker merge semantics, backup files, Skill overwrite/removal.
- `dist/claude-hook.js:1322-1379, 1545-1580, 1764-1895`: resolved options, reflect/fallback bounds, Hindsight attribution and first-prompt injection.

## Implementation consequence

Use the official upstream owner command, preserve the selected defaults above, reject custom `CODEX_HOME`, and preflight conflicting Codex/Hindsight entries before invoking the owner. Keep Hindsight's documented `.hindsight-backup` behavior; do not add another backup/encryption mechanism. Confirm behavior in the parent task's unified test phase.
