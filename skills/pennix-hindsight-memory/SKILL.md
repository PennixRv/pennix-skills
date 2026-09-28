---
name: pennix-hindsight-memory
description: "Use Hindsight for project session memory, explicit cross-project promotion, and user-confirmed long-term memory; keep Trellis and local files authoritative."
---

# Pennix Hindsight Memory

Use this Skill when memory can change a later decision or make a reopened
project session reliable. Hindsight is a semantic memory layer, not the
source of truth for Trellis tasks, Git, current files, credentials, or runtime
state.

## Three memory layers

1. **Project bank** — the registered project bank in `.trellis/config.yaml`.
   The official Hindsight companion may retain/refelect the active session and
   inject bounded recall. Use it for the same project's cross-session memory.
2. **Cross-project memory** — promote only a concise, stable fact from a
   project bank to an explicitly selected shared bank after the user confirms
   the promotion. Never promote merely because a fact sounds reusable.
3. **User memory** — write a stable preference or durable fact only after the
   user explicitly asks for it or confirms the exact proposed text and scope.

Project memory does not automatically become cross-project or user memory.
Current project files, Trellis state, Git, and newer user instructions win
when recalled memory conflicts with a fact that must be implemented or
verified.

## Retrieve and record

- Prefer the official Hindsight companion's bounded recall for ordinary active
  work; do not build a second search client, cache, ledger, scheduler, or
  transcript mirror.
- Record only a semantic delta: objective, constraint, decision, reversal,
  verification, failure lesson, blocker, or next safe action that changes
  future work. Keep routine exploration local to the current task.
- Store a concise fact with its project/task scope and stable source reference.
  Do not store raw transcripts, tool output, credentials, private keys, tokens,
  session handles, database files, logs, or temporary paths.
- When correcting a stored fact, update the same stable document identity or
  use Hindsight's native deletion path; do not create bilingual or rewritten
  duplicates for the same fact.

## Formal handoff

`pennix-session-handoff` owns the explicit handoff boundary. Its default
`hindsight_required` path writes the semantic capsule to the registered
project bank with a deterministic document/operation ID, waits only for the
bounded Hindsight operation, and verifies retrieval of the same document
identity. The local lifecycle receipt stores the capsule digest, operation and
document identity, and retrieval count as separate proof references; it never
claims canonical content equality from semantic recall and never stores the
token or capsule. `core_only` is allowed only when explicitly selected; it does
not claim that Hindsight was written.

Hindsight API calls for this proof are a native owner operation. Do not wrap
them in FastCtx, a shell HTTP fallback, a generic retry loop, or an unrelated
MCP proxy.

## Subnodes and degradation

- Subnodes do not write Hindsight directly unless the current Trellis task
  explicitly grants that ownership. They return a durable report to the
  coordinator, which decides whether the result belongs in project, shared,
  or user memory.
- Hindsight unavailable, empty, stale, or timed out: report the missing memory
  evidence and continue with current files and Trellis control facts. Never
  fabricate recall or silently promote the scope.
- Deployment, token injection, bank registration, uninstall, and component
  verification belong to `$pennix-workflow-lifecycle`; this Skill does not
  edit system configuration.
