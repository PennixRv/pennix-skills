---
name: pennix-cognee-memory
description: "Use the official Cognee Codex plugin for project session memory and explicit cross-project or user promotion while Trellis and local files remain authoritative."
---

# Pennix Cognee Memory

Use this Skill when a memory can change a later decision or make a reopened
project session reliable. Cognee is a memory service, not the source of truth
for Trellis tasks, Git, current files, credentials, or runtime state.

## Scope

- **Project/session memory:** use the explicitly registered dataset for the
  current canonical project root. Keep the originating session, task, and
  project identifiers in every durable record.
- **Cross-project knowledge:** promote only a concise, stable fact after the
  user explicitly confirms the target scope. Include source project, source
  session or task, timestamp, and applicability.
- **User memory:** write a stable preference or durable fact only after the
  user explicitly asks for it or confirms the exact text and scope. Use the
  reserved `pennix-user-penn` project and `type=preference`.

Project memory never automatically becomes cross-project or user memory.
Current files, Trellis state, Git, and newer user instructions win whenever a
recalled result conflicts with a fact that must be implemented or verified.

## Official integration

Use the official `cognee@cognee` Codex plugin for ordinary automatic capture,
recall, session context, and improvement. Pennix owns only the launcher policy,
project registration, formal handoff proof, and workflow routing. The plugin
uses the private `~/.cognee/.env` file and `COGNEE_BASE_URL` plus
`COGNEE_API_KEY`; it talks to Cognee over HTTP and has no MCP server to add.

The lifecycle configures the pinned official plugin and sets
`COGNEE_MANAGED_ENDPOINT=true` so a managed endpoint cannot silently fall back
to a local server. Project isolation sets `COGNEE_SHARED_AGENT_MEMORY=false`.
Only explicitly registered projects may enable the plugin through the Pennix
launcher. A subnode inherits the parent environment but is disabled by the
Trellis subnode policy unless its task grants it ownership.

## Capture and retrieval discipline

Record semantic deltas: objective, constraint, decision, reversal,
verification, failure lesson, blocker, or next safe action that changes future
work. Keep content concise and human-readable. Never store raw transcripts,
tool output, credentials, private keys, tokens, session handles, databases,
logs, or temporary paths. The official capture redaction and sensitive-path
filters remain enabled.

Treat ordinary Cognee recall as candidate evidence. Verify project and session
scope against Trellis and current files before using it. For a strict project
fact, use the registered dataset and exact raw read. Important writes require a
read-back from the authenticated central service; a client success response
alone is not persistence proof. Correct stale facts through the official
update or forget path; do not add rewritten duplicates.

## Formal handoff

`pennix-session-handoff` owns the explicit handoff boundary. Its default
`cognee_required` path sends the semantic capsule to the registered dataset,
then proves the returned Cognee **data UUID**, dataset UUID, metadata digest,
and exact raw content. The local receipt stores only non-secret proof
references. `core_only` is allowed only when explicitly selected and never
claims that Cognee was written.

Cognee API calls for this proof are a native owner operation. Do not wrap them
in FastCtx, a shell HTTP fallback, a generic retry loop, or an unrelated proxy.

## Degraded operation

If Cognee is unavailable, empty, stale, or timed out, report missing memory
evidence and continue with current files and Trellis control facts. Never
fabricate recall or silently promote scope. Deployment, secret injection,
project registration, uninstall, and verification belong to
`$pennix-workflow-lifecycle`; this Skill does not edit system configuration.
