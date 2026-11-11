# Default Pennix Trellis workflow setup

## Goal

Make the existing `pennix-trellis-setup` entry default an ambiguous Trellis
initialization request to the published Pennix Codex workflow profile.

## Requirements

- Default new-project setup uses native `trellis init` with
  `codex-subnode-channel` and `gh:PennixRv/marketplace#v0.6.22`.
- An explicit `native`, another workflow, or another marketplace source wins
  over the Pennix default.
- Existing projects use the native dry-run/update and `.new` workflow-preview
  paths; no `--force`, silent workflow replacement, or user configuration
  mutation is allowed.
- This remains one short user-level entry Skill. It must not copy templates,
  task schemas, report formats, worker lifecycle, or initialize a second
  runtime.

## Acceptance Criteria

- [ ] The Skill is valid and describes the default, explicit override, and
  existing-project routes without ambiguity.
- [ ] The repository boundary document matches the selected default policy.
- [ ] A fresh Git project accepts the exact pinned native CLI initialization
  command and contains the expected Trellis-managed assets.
- [ ] The released source is installed into the existing Pennix Skills
  collection and matches its source checkout.
