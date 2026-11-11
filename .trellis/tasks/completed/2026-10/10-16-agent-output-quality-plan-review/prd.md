# Agent 输出质量与批准前方案审查

## Goal

实现输出质量 Skill 与独立的批准前方案审查闸门，保持既有生命周期和语言 Skill 边界。

## Requirements

- Add `pennix-agent-output-quality` as an independently discoverable Skill for daily replies, progress updates, research and decision reports, task delivery, and pre-approval plan presentation.
- Keep the Skill responsible for information coverage, proportionate detail, emphasis, structure, table selection, Mermaid relation selection, and semantic review. Keep language fidelity, lifecycle state, authorization, installation, and persistence with their existing owners.
- Add one minimal cross-component routing entry that combines the output-quality Skill with `pennix-chinese-tech-writing` only when the delivery is complex or written Chinese content also needs language review. Simple facts remain on the short path.
- Register the new Skill in the `pennix-skills` lifecycle collection contract so native staging, verification, replacement, and readback can manage it.
- Add an independent planning review gate to `pennix-decision-grill`. The gate runs after a plan and its task artifacts form and before the final approval question; evidence or contract defects are corrected or overturned directly, user-owned tradeoffs go through the native grill, and the review repeats until no material issue remains.
- Preserve the existing final plan display, seal/approve/start authorization, Trellis state model, Chinese writing Skill, writing-shape/fragments, FastCtx routing, and client/plugin scope.

## Acceptance Criteria

- [x] The new Skill has valid frontmatter, a discriminating automatic description, discoverable conditional reference material, and no unfinished scaffold.
- [x] The output-quality Skill and routing entry preserve short replies and the existing language/lifecycle boundaries.
- [x] The decision-grill gate documents its review inputs, defect classes, user-choice path, repeat condition, pass condition, and no-second-state-machine boundary.
- [x] Existing decision-grill and workflow-routing contract tests pass with meaningful assertions for the new contracts.
- [x] The lifecycle catalog names the exact new Skill and source path; collection tests pass.
- [x] Source and documentation links, Chinese copy checks, JSON parsing, Skill validation, relevant tests, and full lifecycle tests pass.
- [x] The source changes are committed and pushed; the root coordination task records the source commit, lifecycle materialization, readback, and acceptance evidence.

## Notes

- Root coordination task: `/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-16-agent-output-quality-research`.
- The two deliverables are intentionally independent within one task: output-quality behavior and the pre-approval planning gate have separate owners and acceptance evidence.
- This task is change-bearing and requires `design.md` and `implement.md` before its native start gate.
