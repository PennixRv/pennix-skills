# Align Trellis Setup Skill Ownership

## Goal

Keep user-level Pennix Skills limited to cross-project discovery and native
Trellis setup while moving task-scoped research recording into Trellis itself.

## Requirements

1. Retire the user-level `trellis-research-record` Skill and references that
   imply it is globally available.
2. Add one concise user-level entry point for requests to initialize, refresh,
   or explicitly switch a Trellis workflow in a Codex project. It must call the
   native CLI and must not copy Trellis templates, task schemas, worker rules,
   or fix a marketplace choice.
3. Keep the current Hikari-first/fallback contract intact while directing
   Trellis task research to the project-bundled Skill.
4. Confirm the collection installer removes the retired deployed Skill and
   installs the new entry point.

## Out Of Scope

- Changing Trellis source, user-level `AGENTS.md`, a project workflow's
  content, a marketplace workflow, or any runtime Channel behavior.
- Adding a second installer, registry, configuration key, or setup script.

## Acceptance Criteria

- [ ] The source collection exposes `pennix-trellis-setup` and no longer
  exposes `trellis-research-record`.
- [ ] The setup Skill delegates setup and custom workflow selection to native
  Trellis commands without a fixed workflow choice or force overwrite.
- [ ] Routing and Hikari references identify the project-bundled record Skill.
- [ ] Installer tests and `install.py --check` pass; deployment atomically
  replaces the current collection at the configured discovery root.
