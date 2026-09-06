---
name: codex-hook-registration
description: Register an explicitly reviewed user-level Codex Hook fragment in CODEX_HOME/hooks.json without modifying config.toml or trust state.
metadata:
  short-description: Register reviewed user-level Codex hooks
---

# Codex Hook Registration

Use this Skill only when a component has been explicitly reviewed and its
user-level Codex Hook fragment is ready to install. This Skill does not install
the component, inspect or alter plugin caches, modify project `.codex/` Hooks,
or trust Hooks on the user's behalf.

## Important boundary

- User-level registrations go to `${CODEX_HOME:-$HOME/.codex}/hooks.json`.
- `config.toml` remains the home for `[features].hooks` and Codex's own runtime
  state. Never move `[hooks.state]` into JSON; it is Codex-managed trust state,
  not a Hook definition.
- If the target user `config.toml` contains an inline `[[hooks.*]]` definition,
  stop and resolve that conflict explicitly. `[hooks.state]` is not a conflict.
- Project-level and plugin-bundled Hooks stay in their owning project or plugin.

## Register a reviewed fragment

The fragment must use the native Codex shape, for example:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/reviewed-hook.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Validate without changing the host:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/codex-hook-registration/scripts/register.py" \
  validate --fragment "/path/to/reviewed-hooks.json"
```

Merge idempotently into the user-level file:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/codex-hook-registration/scripts/register.py" \
  merge --fragment "/path/to/reviewed-hooks.json"
```

Use `--dry-run` to inspect the merge first. The command preserves existing
top-level metadata and Hook entries, rejects malformed fragments and unknown
inline user registrations, writes atomically, and sets the destination mode to
`0600`.

## Migrate inline user Hooks

If a component already added `[[hooks.<event>]]` tables to the user
`config.toml`, preview the migration first:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/codex-hook-registration/scripts/register.py" \
  migrate
```

Only supported Codex lifecycle event tables are migrated. `[hooks.state]` and
all other TOML sections remain untouched. After reviewing the preview, apply
the migration explicitly:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/codex-hook-registration/scripts/register.py" \
  migrate --apply
```

The migration is intentionally not automatic and does not delete an unknown
or unsupported Hook table. If the TOML rewrite fails, it restores the prior
`hooks.json` (or removes the file created by this attempt), then exits with an
error. Stop and inspect both files before retrying.

## After registration

Start or restart Codex and use `/hooks` to review and trust the exact current
Hook definition. A successful file merge does not mean Codex has activated a
new non-managed Hook. If the component installer writes `config.toml` by
itself, do not silently clean it; stop, record the exact component behavior,
and use an installation path that separates runtime installation from Hook
registration.
