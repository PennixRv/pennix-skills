# Implementation and Verification Plan

## Ordered Work

1. Confirm the clean source state, read the repository rules and current contracts, and compare the root coordination task with the component targets.
2. Add the new output-quality Skill, conditional reference, and provenance record.
3. Add the minimal routing entry and lifecycle catalog member/path.
4. Add the independent decision-grill planning review gate and focused contract assertions.
5. Run Skill validation, JSON parsing, link checks, copy-rule checks, targeted contract tests, and the full lifecycle test suite.
6. Review the complete diff against the two independent deliverables and acceptance criteria. Fix only in-scope mechanical findings.
7. Commit the component source changes and push the source repository. Record the resulting commit for the root coordination task.
8. Use the native lifecycle/skill-installer staging, verification, replacement, and readback path. Do not hand-edit the installed collection.

## Required Checks

- `skill-creator` quick validation for the new Skill.
- Existing `pennix-decision-grill` and `pennix-workflow-routing` contract tests.
- `component-versions.json` JSON parsing and the full `pennix-component-lifecycle` test suite.
- Explicit local-link and fixed-source SHA checks.
- `pennix-chinese-tech-writing` copy-rule lint on the changed Chinese documents; warnings and style advice remain subject to human review.
- `git diff --check` and final full-scope `trellis-check` review.

## Rollback

Before collection replacement, preserve the verified source commit and active collection receipt. If source checks or staging fail, keep the previous installation and report the original failure. If materialization fails, use the lifecycle owner’s transactional rollback; do not edit the active collection manually. A source rollback reverts the component commit while keeping task evidence.
