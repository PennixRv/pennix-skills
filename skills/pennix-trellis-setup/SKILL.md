---
name: pennix-trellis-setup
description: Initialize, refresh, or select a Trellis workflow for a Codex project through the native Trellis CLI. Use when the user asks to set up Trellis or a custom Trellis workflow in the current project; do not use to modify Trellis source or project-specific workflow rules.
---

# Pennix Trellis Setup

Use Trellis as the source of setup behavior. This Skill selects the Pennix
profile by default and calls the native CLI; it does not copy Trellis templates,
task schemas, Channel rules, or workflow lifecycle.

1. Identify the target project and read its existing `AGENTS.md` and `.trellis/` state. Confirm `trellis --version`; inspect native help when flags or workflow names matter.
2. Unless the user explicitly requests `native`, another workflow, or another marketplace source, an initialization/setup request means the Pennix Codex profile. For a project without `.trellis/`, run:

   ```bash
   trellis init --codex --yes \
     --workflow codex-subnode-channel \
     --workflow-source gh:PennixRv/marketplace#v0.6.22
   ```

   Pass an explicit alternative selection through the same native command instead of combining it with the Pennix default.
3. For an existing project, distinguish the requested operation:
   - Refresh only: run `trellis update --dry-run`, then use the native update path after reviewing its plan.
   - Initialize or select the default Pennix profile: list the pinned source, then create a reviewable candidate:

     ```bash
     trellis workflow --list --marketplace gh:PennixRv/marketplace#v0.6.22
     trellis workflow --template codex-subnode-channel \
       --marketplace gh:PennixRv/marketplace#v0.6.22 --create-new
     ```

     Review `.trellis/workflow.md.new`; do not force-overwrite a modified workflow or project instruction file.
4. Verify `.trellis/workflow.md` (or the reviewed `.new` candidate), the managed `TRELLIS` block in `AGENTS.md`, `.trellis/agents/subnode.md`, `.trellis/scripts/subnode_artifact.py`, and `.agents/skills/trellis-channel/`. Report missing Codex Hook prerequisites; do not edit `config.toml` or Hook trust.

Trellis initialization creates `AGENTS.md` when absent. When it already exists, the native managed-block path must preserve text outside the `TRELLIS` markers. Do not place project Channel or task rules in user-level `AGENTS.md`.
