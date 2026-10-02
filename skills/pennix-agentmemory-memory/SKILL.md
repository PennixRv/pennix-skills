---
name: pennix-agentmemory-memory
description: "Use AgentMemory for project session memory and explicit cross-project or user memory promotion while Trellis and local files remain authoritative."
---

# Pennix AgentMemory Memory

Use this Skill when a memory can change a later decision or make a reopened
project session reliable. AgentMemory is a memory service, not the source of
truth for Trellis tasks, Git, current files, credentials, or runtime state.

## Scope is explicit

1. **Project/session memory** — use the registered project name for the
   current canonical root. Session observations and handoff capsules must keep
   their original session and project identifiers.
2. **Cross-project knowledge** — promote only a concise, stable fact after the
   user explicitly confirms the target scope. Include the source project,
   source session or task, timestamp, and applicability in the content.
3. **User memory** — write a stable preference or durable fact only after the
   user explicitly asks for it or confirms the exact text and scope. Use the
   reserved `pennix-user-penn` project and `type=preference`.

Project memory never automatically becomes cross-project or user memory.
Current files, Trellis state, Git, and newer user instructions win when a
recalled memory conflicts with a fact that must be implemented or verified.

## Retrieve and record

- Prefer the official AgentMemory plugin and MCP tools for ordinary recall and
  capture; do not build a second search client, cache, transcript mirror, or
  scheduler.
- Official recall/smart_search has no project filter. Treat its results as
  shared candidates and verify the project/session before using them. For a
  strict project fact, use the native REST project's memories and exact read.
  The handoff adapter consumes the private registry; official hooks still use
  their own explicit project env or Git-root basename. Same-name projects need
  an explicit consistent project name at launch; registry alone does not alter
  upstream hooks or automatic consolidation scope.
- A successful MCP save alone does not prove central persistence: upstream
  0.9.29 can fall back locally after some remote errors, even with FORCE_PROXY.
  Read important writes back from the authenticated central service.
- Official hooks require the Codex parent process to inherit the private
  client.env variables and native hook trust. A login shell health check does
  not prove that the host has that environment or that capture ran. Lifecycle
  configures fixed MCP with Node --env-file; hooks retain the native launch
  requirement. Never copy hooks or change plugin caches to mask it.
- Record only a semantic delta: objective, constraint, decision, reversal,
  verification, failure lesson, blocker, or next safe action that changes
  future work. Keep routine exploration local to the current task.
- Store concise, human-readable content with project/task/session scope and a
  stable source reference. Never store raw transcripts, tool output,
  credentials, private keys, tokens, session handles, databases, logs, or
  temporary paths.
- Correct a stored fact through AgentMemory's native update/forget path. Do
  not create bilingual or rewritten duplicates for the same fact.

## Formal handoff

`pennix-session-handoff` owns the explicit handoff boundary. Its default
`agentmemory_required` path writes the semantic capsule to the explicit
project with `type=workflow`, then reads the returned memory id and verifies
exact project, type, and content equality. The local receipt stores only
non-secret proof references. `core_only` is allowed only when explicitly
selected and never claims that AgentMemory was written.

AgentMemory API calls for this proof are a native owner operation. Do not wrap
them in FastCtx, a shell HTTP fallback, a generic retry loop, or an unrelated
MCP proxy.

## Subnodes and degradation

- Subnodes do not write AgentMemory directly unless the current Trellis task
  explicitly grants that ownership. They return a durable report to the
  coordinator, which decides whether the result belongs in project, shared,
  or user memory.
- AgentMemory unavailable, empty, stale, or timed out: report missing memory
  evidence and continue with current files and Trellis control facts. Never
  fabricate recall or silently promote scope.
- Deployment, secret injection, project registration, uninstall, and
  verification belong to `$pennix-workflow-lifecycle`; this Skill does not
  edit system configuration.
