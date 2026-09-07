---
name: pennix-trellis-setup
description: Initialize, refresh, or select a Trellis workflow for a Codex project through the native Trellis CLI. Use when the user asks to set up Trellis or a custom Trellis workflow in the current project; do not use to modify Trellis source or project-specific workflow rules.
---

# Pennix Trellis Setup

Use Trellis as the source of setup behavior. This Skill provides the user-level entry point; it does not copy Trellis templates, task schemas, Channel rules, or workflow lifecycle.

1. Identify the target project and read its existing `AGENTS.md` and `.trellis/` state. Confirm `trellis --version` and inspect `trellis init --help` or `trellis workflow --help` when flags or workflow names matter.
2. For a project without `.trellis/`, run native initialization for Codex:

   ```bash
   trellis init --codex --yes
   ```

   When the user explicitly names a workflow or marketplace source, pass that exact `--workflow` and optional `--workflow-source` to the same command. Do not invent a fixed marketplace or workflow selection.
3. For an initialized project, use `trellis update` to refresh managed assets. Change a workflow only when the user explicitly requests it, using `trellis workflow --template <id>` and the requested marketplace source when applicable. Do not force-overwrite a modified workflow or project instruction file.
4. Verify `.trellis/workflow.md`, the managed `TRELLIS` block in `AGENTS.md`, and the project-scoped `.agents/skills/` entries. Use the installed project instructions for ordinary work after setup.

Trellis initialization creates `AGENTS.md` when absent. When it already exists, the native managed-block path must preserve text outside the `TRELLIS` markers. Do not place project Channel or task rules in user-level `AGENTS.md`.
