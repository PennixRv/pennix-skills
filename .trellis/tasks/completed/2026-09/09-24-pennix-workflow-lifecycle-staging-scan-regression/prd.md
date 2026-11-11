# Fix lifecycle staging sibling discovery regression

## Requirements

- `discover` must scan direct children of `CODEX_HOME/skills`, the parent of the live `pennix-skills` collection.
- Names beginning with `.pennix-skills-stage` are reported by basename with `unknown` status and never traversed, adopted, or deleted.
- `verify` keeps these observations advisory and non-blocking.
- Add a regression test using a sibling staging directory; publish the patch and reinstall from `pennix-skills/main`.

## Acceptance Criteria

- [ ] Existing sibling staging candidates are visible in final installed `discover` output.
- [ ] Full `verify` remains `match` with the candidate reported only in `advisories`.
- [ ] All source tests pass, version is published, and both repositories are clean.

## Goal

Correct staging sibling discovery under the Skills parent, add regression coverage, publish the patch, and reinstall the final collection.

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
