---
name: pennix-worktime-memory
description: "Maintain high-value OpenViking semantic context during an active task, including recall, experience lookup, task research notes, and explicit durable memory writes; do not use for ordinary conversation or transcript archiving."
---

# Pennix Worktime Memory

Use during an active Trellis task when a conversation produces information that
will change later understanding or action. The official OpenViking Codex
Plugin owns automatic session capture, recall, commit, and background
extraction. This skill adds the missing worktime decision: when to retrieve
more context and when to record a concise task-scoped semantic note.

## Retrieve

- Use already injected OpenViking context when it answers the current question.
- For complex executable work, recovery, a similar failure, a historical
  reference, or a user mentioning a prior decision, use the official
  `ov-experience-memory` route: search the current user's Experience root,
  then read only relevant canonical URIs.
- Use `find` for ranked triage, `search` for deeper or token-budgeted context,
  and `read` for an important exact URI. Treat `score`, `detail`, `type`, URI,
  and task fit as OpenViking probability signals; do not invent a Pennix
  confidence threshold or convert them into a binary truth flag.
- Current files, Git, tests, Trellis task/ownership and user instructions win
  when memory conflicts with a fact that must be implemented or verified.

## Record

When a high-value signal occurs, update the current task's
`research/worktime-memory.md` with a short readable conclusion and its source.
Use only the sections that matter: objective and user contract; current facts
and assumptions; decisions; rejected or superseded approaches; validation;
completed progress; open work and next safe action; blockers and risks;
external state/resources/watches; and reusable experience.

Triggers include a user-confirmed or changed goal/boundary, an accepted or
rejected design decision, a verification result, a failure lesson, a blocker or
important open item, a meaningful phase boundary, pre-compaction review,
handoff preparation, and completion review. Do not record greetings, repeated
content, raw tool output, or exploration that produced no changed conclusion.

The unit is a meaningful semantic delta, not a turn, time interval, token
count, or tool call. Preserve useful OpenViking URI/score/detail/type or local
path provenance when it changes the conclusion. Do not add a schema validator,
hash, CAS, length limit, scheduler, background worker, transcript mirror, or
second memory database.

## Durable writes and resources

Use OpenViking `remember`/`write` only when the user asks to remember something
or when a clearly stable cross-task preference or experience should survive the
task. Keep routine task notes local to the task. Use `add_resource` and watches
only with explicit approval and an exact intended resource; use official watch
and URI operations for later cancellation or deletion. Never write credentials,
private keys, tokens, full transcripts, raw large outputs, runtime handles, or
private plugin state.

## Handoff and degradation

Before a formal handoff, review this task note and relevant scored recall, then
place useful semantic context in the handoff's free-text Semantic Handoff
Capsule. The capsule supplements, but does not replace, current task facts or
Trellis ownership. It must not be silently truncated.

OpenViking failure, timeout, empty recall, or unavailable MCP affects only the
semantic enhancement. Continue with current files and Trellis control facts,
and state missing memory evidence instead of fabricating successful recall or
convergence.
