# Implementation Plan

1. Add `skills/pennix-trellis-project-update/SKILL.md` using only the verified fork commands, current Pennix workflow semantics, and the ownership boundaries in the research record.
2. Add a small contract test for the Skill's frontmatter, native commands, safe conflict path, source pinning, and owner routing.
3. Add the minimum route references to `pennix-workflow-routing` and `pennix-workflow-lifecycle`; do not add scripts or duplicate the lifecycle catalog.
4. Run Skill validation, focused tests, full repository tests, and `git diff --check`.
5. Review the source diff for accidental project/runtime/credential ownership, then commit and push `main`.
6. Use the system Skill installer to stage every catalog path from the pushed source ref, call the installed lifecycle `replace-staged`, and run component plus full verification.
7. Record the final source commit, remote alignment, staging/replacement receipt, and installed verification in the root coordination task.

Rollback: before release, revert the reviewed source commit; after release, stage the prior source commit through the same lifecycle replacement path. A failed staging or receipt check must leave the live collection untouched.
