---
name: pennix-skills-install
description: Install or update the user-maintained Pennix Skills collection from an explicit local checkout, including its Git submodule Skills. Use only when the user explicitly asks to install or update that collection.
metadata:
  short-description: Install the private Pennix Skills collection
---

# Pennix Skills Install

Install the complete private Skill collection from a known local
`pennix-skills` checkout. This is an explicit deployment action, not an
ordinary-session setup step.

Run the installed helper with the exact source checkout. The default collection
root is `${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/`; callers may set
`PENNIX_SKILLS_ROOT` to another host-selected collection root:

```bash
PENNIX_SKILLS_ROOT="${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}"
python3 "$PENNIX_SKILLS_ROOT/pennix-skills-install/scripts/install.py" \
  --source "/path/to/pennix-skills"
```

The default is only a default, not the only supported discovery root. When the
host uses a different user Skill root, set the collection root explicitly, for
example `$HOME/.agents/skills/pennix-skills`:

```bash
PENNIX_SKILLS_ROOT="${PENNIX_SKILLS_ROOT:-$HOME/.agents/skills/pennix-skills}"
python3 "$PENNIX_SKILLS_ROOT/pennix-skills-install/scripts/install.py" \
  --source "/path/to/pennix-skills" \
  --dest "$PENNIX_SKILLS_ROOT"
```

The helper initializes the checkout's pinned Git submodules, validates every
direct `skills/<name>/SKILL.md`, and installs the collection to
the selected `skills/pennix-skills/` discovery root.

- Do not run it unless the user explicitly requested installation or update.
- Pass an existing checkout. The helper does not create a source checkout,
  change branches, fetch or pull newer refs, or choose component versions.
  When initialization needs a missing object, it may retrieve only the commit
  already pinned by the checkout's Gitlink.
- Use `--check` to verify the source collection and submodule state without
  changing the installation directory. Every submodule must match its pinned
  Gitlink and have no uncommitted content; the parent checkout may otherwise
  be the explicit source the user selected.
- The destination must be a `pennix-skills` directory directly under a
  `skills` directory. This permits host-selected roots such as
  `.agents/skills/pennix-skills` while keeping the collection boundary clear.
  The destination is owned only by this collection. Do not use this helper to
  install an unrelated standalone Skill.
