# Align Pennix Trellis setup with native workflow selection

## Goal

Make Pennix default selection apply only to first initialization and route existing-project refresh or explicit workflow changes through native Trellis semantics without prescribing a private .new migration.

## Requirements

- Keep `pennix-trellis-setup` as a concise user-level routing Skill, not an
  alternative initializer, workflow merger, runtime protocol, or audit Skill.
- Default to the fixed Pennix Codex workflow only when `.trellis/` is absent.
  Use native `trellis init --codex --yes --workflow ... --workflow-source ...`.
- For an existing project, distinguish native refresh from an explicitly
  requested workflow switch. Do not select or overwrite a workflow merely
  because the user said “setup”.
- A requested workflow switch uses native `trellis workflow`. If the native CLI
  reports local edits, surface its protection and obtain explicit approval
  before an overwrite; do not prescribe `--create-new` as a Pennix migration
  flow or implement a private merge process.
- Leave `AGENTS.md` creation and managed-block preservation to native Trellis;
  the Skill must not patch the file itself.

## Acceptance Criteria

- [x] The Skill has one clear uninitialized-project command pinned to the
      released Pennix Marketplace tag.
- [x] Its existing-project route differentiates refresh, explicit switch, and
      protected local edits without adding a wrapper.
- [x] It does not describe `.new` as a Pennix mechanism and remains within the
      source repository's responsibility boundary.
- [x] Skill validation and an isolated native CLI smoke test pass.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.

## Verification

- `quick_validate.py skills/pennix-trellis-setup` passed.
- `trellis init --codex --yes --workflow codex-subnode-channel --workflow-source
  gh:PennixRv/marketplace#v0.6.23` passed in an empty temporary project. It
  created the native `AGENTS.md` managed block and required workflow assets;
  no `.new` file was created.
