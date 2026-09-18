---
name: pennix-workflow-bootstrap
description: Guided deployment entry for the Pennix Codex workflow. Use when the user explicitly asks to bootstrap, inspect, plan, apply, verify, or roll back workflow components; keep project actions plan-only unless separately approved.
metadata:
  short-description: Bootstrap the Pennix workflow safely
---

# Pennix Workflow Bootstrap

Use this Skill only for an explicit workflow deployment request. It is the
single user-facing deployment entry; component setup logic lives in its
internal adapters.

## 两类工作

Bootstrap 必须把系统安装和项目初始化分开显示、计划和确认。系统安装可以部署全局工具，
但不初始化任何特定项目；项目初始化必须携带明确的 `project root`，并单独确认。

### 系统安装

On a fresh Arch Linux host, before Codex or Pennix Skills exists, run:

```bash
bash "/path/to/pennix-skills/skills/pennix-workflow-bootstrap/scripts/seed-arch.sh"
```

The executable may be launched from either `bash` or `zsh`; its Bash shebang
selects the required interpreter. Execute it as a command rather than sourcing
it into the caller shell. The seed reads the adjacent `templates/` directory;
copy the whole `pennix-workflow-bootstrap` directory if relocating it.

It supports native Arch Linux and Arch Linux under WSL2. It installs the
current `openai-codex` candidate from the Arch official repository, prompts
for an OpenAI-compatible `base_url` and a hidden API key, renders the tracked
`templates/config.toml.seed` and `templates/auth.json.seed`, and materializes
the seed-owned fields in `CODEX_HOME/config.toml` and `CODEX_HOME/auth.json`.

The seed refuses to overwrite an existing `CODEX_HOME/config.toml` or
`CODEX_HOME/auth.json`. It does not clone or execute remote Pennix source,
write the key to TOML, print the key, or add the current package candidate to
the fixed component catalog. After a new Codex session starts, install Pennix
Skills, then let bootstrap plan the remaining system installation actions.

The supported host boundary is Arch Linux on Linux: native Arch Linux and
Arch Linux under WSL2. `pacman` handles official repository packages. For AUR
packages, prefer an already-installed `yay`, then fall back to `paru`.
Bootstrap does not install an AUR helper, guess package names, or force
independent/forked components through a package manager. Non-Arch hosts and
unknown/WSL1 environments are discoverable but all write actions are blocked.

After the seed, the system-installation actions are read-only `discover` →
read-only `plan` → explicit named actions with `apply --action <name> --yes` →
fresh `verify`. The plan marks these actions with `category=system-installation`:
Pennix Skills installation, installation-phase `config.toml` fields from
`templates/config.toml.install`, and the tracked `AGENTS.md.install` template.
The config template is the portable static baseline only: it excludes host paths,
project trust, Web location, MCP/plugin state, marketplace state, and hook hashes.

### 项目初始化

Trellis, CodeGraph, and AOE binaries may be installed by system actions, but
their project initialization is a separate `category=project-initialize` plan.
It requires `plan --project-root /absolute/project/path`; it may create `.trellis/`,
`codegraph.json`, indexes, or project workflow assets only after a separate
confirmation. It must never run as a side effect of the seed or Skills install.

During Trellis planning or an explicit `grill-me` gate, show the component key,
source/ref from the catalog, target, risk, precondition, postcondition, and
rollback receipt. Use Codex's native `request_user_input` directly when it is
present in the current session. Do not
probe for it through `functions.exec`, nested `tools.*`, `ALL_TOOLS`, shell, or
MCP. A schema error may be corrected and retried once; host refusal,
cancellation, timeout, or unavailable native interaction falls back to text and
stops the turn. Never auto-select the recommendation. Batch independent
decisions from the same gate when the host allows it; keep dependent decisions
separate. During implementation or apply, do not ask a new question: use the
sealed task/spec decision, or record `decision-needed` and return to planning if
the ambiguity is material.

All component versions and refs come from `references/component-versions.json`.
Do not add a second version table to this Skill or to an adapter. Do not print
secret values, full configuration, sessions, databases, logs, caches, locks, or
runtime state. `rollback` accepts only a receipt created by this bootstrap and
stops if the target hash has drifted.
