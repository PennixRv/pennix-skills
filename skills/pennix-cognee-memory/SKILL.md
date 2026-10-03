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
  user explicitly asks for it or confirms the exact text and scope. Use a separate principal-bound approved user dataset with `kind=preference`.

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
The lifecycle keeps the native plugin disabled in the global Codex config.
Start a project through
`~/.local/bin/pennix-codex` (managed by lifecycle, pointing to the installed
Cognee memory skill launcher) to enable
it only when the canonical Git root is registered and the private service
configuration is ready; that launch also supplies the project's registered
`COGNEE_PLUGIN_DATASET`. Unregistered roots launch with the plugin disabled.
A subnode inherits the parent environment but is disabled by the Trellis
subnode policy unless its task grants it ownership.

## Capture and retrieval discipline

The official plugin captures filtered Q&A and allowed tool traces, then runs
native session feedback, persistence, distillation, graph construction and
recall. These filtered sources may persist long term under the approved full
official chain. Capture redaction and private-path/tool exclusions stay on;
credentials, keys, tokens, database contents, unrelated logs and rollout files
remain excluded. Shell/wrapper tools whose text cannot prove private-path
exclusion are denied by the native capture policy.

Explicit records supplement the automatic chain with an objective, constraint,
decision, correction, verification, failure lesson or next safe action. Keep
these records concise and readable, with task/session/source/time/scope. Do
not duplicate a fact in multiple languages. Use `scripts/memory.py` with the
explicit `--project-root` for remember, recall, raw, revise, revoke/delete,
approved promotion and improve. Cross-project/user `promote` requires the
source data UUID, target scope and an explicit `--approval-ref`; never invent
approval. `revise` verifies the new record before deleting the old source.
Use explicit `--scope cross_project` or `--scope user` on recall, raw, revoke
or delete to manage the already-approved principal dataset. Reads never create
a dataset or merge other project data. The default remains `project`.
Deletion is complete only after raw, graph, session-derived content and recall
absence are checked; a source-delete response alone is insufficient.

At a Trellis stage close or formal handoff, call `improve --session-id <id>` for
the verified Cognee session IDs. It enables native truth-subspace and global
context index for that project's dataset. Inspect every stage status/reason;
a successful HTTP response does not mean each stage succeeded. Personalization
and automatic user-preference extraction remain off.

Treat ordinary Cognee recall as candidate evidence. Verify project and session
scope against Trellis and current files before using it. For a strict project
fact, use the registered dataset and exact raw read. Important writes require a
read-back from the authenticated central service; a client success response
alone is not persistence proof. Correct stale facts through the explicit revision or official forget path;
retain the supersedes/source reference and verify derived absence.

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
