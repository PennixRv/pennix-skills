# Adopt Trellis beta.25 in Pennix Skills catalog

## Goal

Update the canonical trellis-cli catalog entry to 0.7.0-beta.25 and record the owner-side verification needed for global Skills installation.

## Requirements

- Change only the canonical `trellis-cli` entry in
  `skills/pennix-workflow-lifecycle/references/component-versions.json` from
  `0.7.0-beta.24` to `0.7.0-beta.25`.
- Preserve the catalog's owner, delivery, source, action, and collection
  contract fields; do not change unrelated component versions.
- Validate the catalog and lifecycle tests, then commit and push this owner
  change before invoking the system Skill installer.
- Install the catalog's immutable collection from the resulting source commit
  through Codex `$skill-installer`; replace the staged collection only through
  the native lifecycle owner.

## Acceptance Criteria

- [ ] The catalog has exactly the intended Trellis version change and no
  unrelated diff.
- [ ] Owner checks pass and the catalog commit is pushed.
- [ ] The selected Pennix Skills collection is staged from the pushed commit,
  atomically installed at `~/.codex/skills/pennix-skills`, and discoverable.
- [ ] Installed `trellis-cli` and collection receipts report the new source
  and version; private runtime content is preserved.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
