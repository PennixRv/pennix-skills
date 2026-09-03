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

Run the installed helper with the exact source checkout:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/pennix-skills-install/scripts/install.py" \
  --source "/path/to/pennix-skills"
```

The helper initializes the checkout's pinned Git submodules, validates every
direct `skills/<name>/SKILL.md`, and installs the collection to
`${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/`.

- Do not run it unless the user explicitly requested installation or update.
- Pass an existing checkout. The helper does not create a source checkout,
  change branches, fetch or pull newer refs, or choose component versions.
  When initialization needs a missing object, it may retrieve only the commit
  already pinned by the checkout's Gitlink.
- Use `--check` to verify the source collection and submodule state without
  changing the installation directory.
- The destination is owned only by this collection. Do not use this helper to
  install an unrelated standalone Skill.
