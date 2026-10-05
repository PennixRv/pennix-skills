# Clarify verified SiYuan native capability boundaries

## Goal

Owner follow-up to root SiYuan workflow integration: correct kernel-host versus local Codex Skills and persist v3.8.6 native import/export limitations, then publish and install the scoped reference update.

## Requirements and boundaries

- This is the source-owner follow-up to `codex-workflow-optimization/.trellis/tasks/10-05-siyuan-knowledge-workflow-design`; the user already authorized implementation, source publication, and local installation. Scope is one existing capability reference on `main`.
- Distinguish kernel-owned SiYuan Skills, usable through native MCP by external agents, from locally installed Codex/Pennix Skills. Native load returns content/resources without installing or executing them locally.
- Record observed SiYuan v3.8.6 limitations: native SY export/import mismatch, Markdown round-trip scope, Pandoc prerequisite, and asset-path refusal. Preserve native permissions and version-bounded conclusions.
- Do not fork SiYuan, add converters, change credentials/configuration, or copy user notes/runtime records into this repository. Runtime evidence belongs to the root task.
- Publish the reference through the existing system installer and transactional lifecycle collection replacement; do not edit the live collection.

## Acceptance Criteria

- [x] Reference agrees with the verified upstream storage/load paths and the root native capability results.
- [x] Source Skill `quick_validate`, native collection validator, and `git diff --check` pass. Source and staging each match the catalog's exact 11 entries and valid names; staged seed is executable and reference matches source. Two retired directory trees contained only empty directories and were removed precisely; no cache file was removed.
- [x] Source commit `46c3cd6710878039c6467ed9a89692746de0ce79` is pushed on `main`; that immutable revision was staged by the system installer in git mode and installed by native lifecycle replacement.
- [x] Full lifecycle verification reports 14 matching components, matching collection, enabled/configured SiYuan target, and empty failures/advisories. A local owned end-marker placement issue initially blocked verification; root owner repaired only the comment location with unchanged TOML semantics and unrelated hook bytes before the successful verification.
- [ ] Root task records the source/installation evidence; source-owner task is archived with both old and new paths staged correctly.

## Planning Seal

Closed 2026-10-05: bounded documentation follow-up, existing user authorization, main-session delivery, no extra branch or agent. Revert the source reference commit and reinstall that accepted revision if its scoped validation fails. No unresolved implementation choice remains.
