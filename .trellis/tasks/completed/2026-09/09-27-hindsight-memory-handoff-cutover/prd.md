# 迁移 Pennix 记忆路由与 Hindsight handoff 合同

## Goal

为根协调任务 09-27-hindsight-memory-base-migration 实现 Hindsight 项目/跨项目/用户三层政策 Skill，迁移工作流路由和交接精确完成回执，移除 OpenViking 专属 worktime/checkpoint/mode 活动实现并明确拒绝旧 mode。handoff 默认 ready 必须由本次 Hindsight 操作完成和目标 bank 可读证明；core_only 仍仅显式启用。目标分支 main。

## Requirements

- Replace `pennix-worktime-memory`'s OpenViking-specific operations and OpenViking routing rules with one Pennix-owned `pennix-hindsight-memory` policy skill. Keep upstream `hindsight-coding-agent` Skill as tool/API reference; do not duplicate it or create one Pennix skill per memory layer.
- Define three distinct banks and permission rules: project bank (automatic Hindsight Stop write-back only for explicitly registered Trellis projects); cross-project knowledge bank (explicit main-session promotion of verified, source-linked project knowledge); private user bank (only stable facts/preferences the user explicitly asks to remember or confirms). Never route raw project transcripts to cross-project/user banks.
- Keep project files, Trellis task/spec/ownership, current user instructions and local handoff core/receipt authoritative. Hindsight content is candidate/derived context with source and scope; stale/conflicting entries must not override current authority.
- Redesign the existing handoff lifecycle around Hindsight v0.10.1: default `ready` requires this handoff's write to complete and at least one material key fact to be read back from the correct project bank; API errors, queued/failed operations, empty or unrelated recall remain pending/blocked. `core_only` remains explicit only. Remove OV-only `archive_required`/`convergence_required` modes and checkpoint adapter; reject obsolete modes with a clear error, never fallback silently.
- Keep semantic capsule, local receipt, project identity and Trellis ownership; remove the `openviking` field from active core schema/projections and do not migrate existing OV content. Preserve archived history as history.
- Update Pennix workflow routing, lifecycle catalog, handoff schema/CLI/docs/tests and any materialized Pennix Skill roster. Do not modify Hindsight source and do not place policy rules only in the coordinator root.

## Acceptance Criteria

- [ ] One new Pennix Hindsight memory policy skill covers project/cross-project/user layers, source/authority precedence, safe recall, explicit promotion, correction/deletion and limits; the upstream Skill remains the only generic tool/API usage guide.
- [ ] Active Pennix routing, catalog, handoff schema, mode handling and scripts contain no OpenViking-specific branch/adapter/field; archived research/task history is retained and not misrepresented as active runtime.
- [ ] Handoff default write uses authenticated Hindsight API for the registered project bank, waits for completion using the v0.10.1-supported synchronous or operation-status interface, then verifies same-document retrieval for this handoff. Receipt stores only minimal status/IDs/hash/provenance, not transcript or secret; semantic retrieval is not claimed as canonical content equality.
- [ ] `ready` is impossible for API unavailable, operation pending/failed/timed-out, wrong bank, empty/unrelated retrieval or failed retrieval verification. Repeat invocation is idempotent for the same handoff ID; explicit `core_only` remains usable without Hindsight.
- [ ] Core-only legacy mode behavior remains deterministic; obsolete OV modes and obsolete OV-shaped core data fail closed with migration guidance and no automatic memory import.
- [ ] Contract tests cover correct/incorrect bank, async/sync operation state, timeouts, unavailable service, retries, deduplication, unrelated retrieval, `core_only`, old modes, and no secret/content persistence. Tests run only in the parent's unified post-implementation phase.
- [ ] Pennix `main` release/install and root-consumer evidence confirm updated routing/Skills/handoff assets; no API secret or real conversation enters Git.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
