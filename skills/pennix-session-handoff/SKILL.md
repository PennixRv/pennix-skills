---
name: pennix-session-handoff
description: Create, validate, or render one explicit, timestamped Pennix session handoff package with a semantic handoff capsule and local rollout projection. Use only for a current user-requested formal cross-session handoff.
---

# Pennix Session Handoff

This Skill creates a navigation package for a new Codex coordinator
session. It is not a transcript backup, task database, checkpoint ledger,
native session resume, or mechanism for continuing an interrupted tool call.
Trellis remains the source of truth for task and lifecycle state; the new
session must verify those facts again.

Do not use it for ordinary work, restart, compaction, waiting, acceptance
failure, provider failure, or a lost transport handle. Those events do not
authorize a handoff.

When the current user explicitly requests a formal handoff, first finish and
verify the work that must be visible to the next session. Prepare a small
request JSON outside `.trellis/session-handoffs/`. The exact top-level fields
are:

```json
{
  "session_label": "short description of this session",
  "facts": ["verified fact with a stable project source"],
  "evidence_paths": ["AGENTS.md", ".trellis/workflow.md"],
  "next_action": "next action for the new coordinator",
  "blockers": [],
  "risks": ["known residual risk"],
  "validation": [{"command": "check name", "result": "result"}],
  "memory_projection": {
    "semantic_capsule": "task contract, scene, decisions, reversals, validation, experience, blockers, and open work",
    "local": [], "archive_refs": [], "openviking": []
  },
  "rollout": {
    "path": "/absolute/path/to/the-current-codex-rollout.jsonl",
    "session_id": "optional-host-session-id"
  }
}
```

`evidence_paths` must be existing project-relative non-runtime files. The
rollout path is deliberately explicit and absolute: never scan a session
directory or choose a file by modification time. Do not put credentials, raw
tool output, transcript text, cache paths, or temporary state in the request.
The helper scans the rollout locally as a streaming JSONL source, binds the
completed-record prefix by byte boundary, inode and SHA-256, and only projects
eligible public user/assistant messages plus finite tool metadata. The source
may be large. It excludes
reasoning, developer/system messages, raw tool arguments, unbounded output and
credentials. File order is the timeline order; record timestamps are auxiliary
only. A later explicit user correction is kept with the earlier event instead
of silently overwriting history.

Run:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" --project-root . \
  write --request <request.json> --explicit-user-request
```

`write` emits the only package identifier and JSON path. It uses the fixed UTC
format `YYYYMMDDTHHMMSSffffffZ` and writes exactly one paired package under:

```text
.trellis/session-handoffs/<handoff-id>/session-handoff.json
```

It fails on a timestamp-directory collision and never overwrites an earlier
package. It records a task snapshot, Git history, content digests for the
requested evidence, and a rollout coverage/candidate projection. It does
not upload rollout content or call external models.

To inspect one package later without writing, use the exact emitted path:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" \
  --project-root . validate --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

`ready` validates the package itself, not continued sameness of the source
worktree. Current task, Git, evidence, rollout, and late OpenViking extraction
are reconciled by the target session; they do not silently rewrite the capsule
or block package consumption. This Skill never changes task status, controls
Trellis workers, or copies a conversation, credential, cache, or runtime ledger.

## Lifecycle Receipt And Retention

The immutable core is deliberately not a consumed-state database. A separately
append-only local receipt may record source convergence, target reconciliation,
and retention. It lives outside Git at:

```text
.trellis/.runtime/handoff-lifecycle/<handoff-id>.jsonl
.trellis/.runtime/handoff-archive/<handoff-id>/
```

For the following examples, set the existing helper path once:

```bash
PENNIX_HANDOFF="${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py"
```

Use these commands only as part of the user's explicit formal-handoff request:

```bash
python3 "$PENNIX_HANDOFF" --project-root . prepare --handoff <core.json> --mode core_only
python3 "$PENNIX_HANDOFF" --project-root . finalize --handoff <core.json> --observation <project-relative-proof.json>
python3 "$PENNIX_HANDOFF" --project-root . admit --handoff <core.json> --attestation <project-relative-attestation.json>
python3 "$PENNIX_HANDOFF" --project-root . retention archive --handoff <core.json> --confirm-handoff-id <handoff-id>
```

`PENNIX_HANDOFF` above abbreviates the existing `handoff.py` path used in the
earlier commands. `prepare` fixes one mode and writes no remote state.
`finalize` consumes only a local observation manifest. It never reads
Plugin private state, calls shell HTTP, or retries forever. `core_only` is the
default and needs no remote proof. `capsule_required`, `archive_required`, and
`convergence_required` require their respective verified exact-read proof
digests; unavailable official capability must remain `unsupported`,
`unavailable`, or `pending`, never silently downgrade.

`admit` records only that the target session completely read the paired JSON
core and prompt, ran `$trellis-start`, and reconciled current facts. Its `target_source`
must exactly equal the current Trellis direct source `session:<target-key>`.
The source rollout `session_id` is provenance only and is rejected as target
identity. Admission never executes the pending action, starts a task, changes
a task pointer, or closes a task. A later, separately authorized continuation
uses native Trellis `task.py start` for an incomplete task and then rechecks
its direct current source. A completed task instead follows native Trellis
finish/archive by exact task path; do not manufacture a session pointer.

After a reconciled admission, `retention archive` copies only the exact core
and paired prompt using copy-first validation. `restore`, `reopen`, and
`purge` require the exact same handoff id confirmation. `purge` removes only
the canonical core/prompt after archive verification; it never deletes task,
rollout, session, memory, resource/watch, log, or remote data. The receipt is
kept as audit evidence. Run `status --handoff <core.json>` to inspect whether
the selected lifecycle mode is ready; the prompt renderer rejects a pending
high-assurance mode.

## New-Session Handoff Closure

The package has one lifecycle admission commit for the target. In the target
session, “close the handoff” means reconcile the captured task with current
Trellis facts before resuming work:

1. Validate the exact package and stop unless the receipt is `ready`.
2. Read the paired JSON core and `session-handoff-prompt.md` completely before acting on its
   pending next action.
3. Run `$trellis-start` and compare the captured task, Git state, evidence,
   and pending action with current project facts. Record one `admit`
   attestation only after that reconciliation, with `action_authorized=false`.
4. If the captured task is now actually complete, use the normal
   `$trellis-finish-work` flow to finish and archive it before doing other work.
5. If it is incomplete, changed, or blocked, do not close it from the handoff
   snapshot; record the current disposition and use `$trellis-continue` only
   when continuing that task is appropriate.
6. Stop after this reconciliation. Do not execute the pending next action or
   begin new implementation until the user gives a subsequent instruction.

The admission commit is at-most-once per handoff: an incomplete read, timeout,
network/model interruption, or process exit before the receipt append is not a
consumption. The same target may retry and receives an idempotent result after
success; a different target cannot replace the first successful consumer.
After successful admission, package retention archive is independent and may
be retried without consuming the asset again. Session-internal compaction and
ordinary restart only resume the target's current task and do not repeat a
successful admission.

The package is a navigation hint. A `ready` receipt never proves that a task
is complete and never authorizes closing an unrelated current task. A source
rollout session id never binds the target Trellis task.

## Task Ownership Transfer

When the handoff contains a task, the package lifecycle and Trellis task
ownership are separate but must be advanced in this order. These orchestration
commands call the project's native `.trellis/scripts/task.py ownership`
implementation; this Skill never edits task pointers itself:

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership quiesce --handoff <core.json> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership seal --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . finalize --handoff <core.json> --observation <proof.json>
python3 "$PENNIX_HANDOFF" --project-root . ownership retire --handoff <core.json> --expected-generation <n> --archive-observation <not_required|observed> --explicit-user-request
```

`retire` is the source barrier: Trellis records `retiring`, removes and
verifies the source session pointer, then exposes `ready`. An interrupted
retirement remains non-claimable and can be recovered only by the same source
identity. High-assurance modes require their verified source observation first;
missing OpenViking or Task API evidence remains `pending`/`unsupported`.

After a new session has completed the read-only intake above and the user
explicitly authorizes continuation, it may claim and close ownership:

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership claim --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership consume --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership archive --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership status --handoff <core.json>
```

The target must have its own direct `session:<key>` identity and no current
task; it never inherits the source pointer. `claim`, `consume`, and ownership
`archive` are distinct, generation-checked, idempotently recoverable states.
Ownership archive is only a local receipt and differs from handoff
`retention archive`, which copies the immutable core and prompt. Neither
operation executes `pending.next_action`, closes the Trellis task, writes
OpenViking state, or deletes sessions, memory, resources, watches, rollout, or
logs.

When the user also asks for the new-session entry prompt, render it only after
that exact `validate` reports `ready`:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root> \
  --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

The renderer atomically creates the paired
`session-handoff-prompt.md` in the same timestamp directory. Standard output
contains only a labeled, fenced short new-session entry prompt, not the
complete handoff. After a complete `write -> validate=ready -> render`, return
that standard output unchanged as the final delivery, so the user can copy the
`text` block directly into a new Codex session. Do not append a summary,
validation narration, or further command after that block.
The complete prompt directs the new session to validate again, then use the
normal `$trellis-start` flow, reconcile the captured task, and only then use
`$trellis-finish-work` or `$trellis-continue` according to current facts. Its
task and next action are navigation hints that never override current user
instructions, Trellis facts, Issue state, or Git state. After rendering a
ready-only prompt, stop; do not run `finish`/`archive` or any other mutation
that would invalidate the receipt. A later session can continue only after its
own validation and normal Trellis startup checks. The initial takeover stops
after reconciliation; it does not automatically execute the pending action.
