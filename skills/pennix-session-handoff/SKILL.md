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
The helper scans the rollout locally as a streaming JSONL source to the capture
boundary and projects eligible public user/assistant messages plus tool metadata.
The source may be large: no package text, record, candidate, or receipt length
limit is imposed. It excludes reasoning, developer/system messages, raw tool
arguments, raw tool output, and credentials. File order is the timeline order;
record timestamps are auxiliary only. A later explicit user correction is kept
with the earlier event instead of silently overwriting history.

The package JSON is the canonical complete asset. Its paired Markdown prompt is
a compact navigation view: it preserves lifecycle instructions, verified facts,
the semantic capsule, memory references, and pending work, while referring to
the complete `conversation.timeline`, `conversation.candidates`, and
`conversation.coverage` fields in the core instead of duplicating them. This
avoids wasting new-session context without truncating or discarding any handoff
data; read both files completely during admission.

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
package. It records a task snapshot, Git history, requested evidence paths, and
a rollout coverage/candidate projection. It does
not upload rollout content or call external models.

To inspect one package later without writing, use the exact emitted path:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" \
  --project-root . validate --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

`ready` validates the package itself, not continued sameness of the source
worktree. `core_only` does not require remote proof, but still waits for the
final observed source boundary and canonical JSON/prompt pair. When a handoff
contains a task, its existing Trellis quiesce/seal receipt is also required.
Current task, Git, evidence, rollout, and late OpenViking extraction are
reconciled by the target session. Higher-assurance modes additionally require
their selected source proof before admission; a target attestation cannot
bypass that source gate. Neither path silently rewrites the capsule. This
Skill never changes task status, controls Trellis workers, or copies a
conversation, credential, cache, or runtime ledger.

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
Render the paired prompt after `write -> validate=ready` and before
`finalize`; `finalize` rejects a missing or unreadable pair. It consumes only
a local observation manifest, never reads Plugin private state, calls shell
HTTP, or retries forever. `core_only` is the default and needs no remote
proof, but still requires the sealed final source boundary. When a captured
task exists, run the native ownership `quiesce` and `seal` commands before the
final ready check. `capsule_required`, `archive_required`, and
`convergence_required` require their respective verified proof references;
unavailable official capability must remain `unsupported`, `unavailable`, or
`pending`, never silently downgrade.

`admit` also checks the prepared mode's current source state. A valid target
attestation cannot turn a `pending` source into a reconciled admission; it is
recorded as blocked and can be retried after `finalize` records the required
source proof. Source readiness and target reconciliation are separate receipt
axes.

`admit` uses one cumulative target attestation in this fixed order: complete
JSON core read, paired prompt read, `$trellis-start`, then current-fact
reconciliation. An incomplete prefix records `admitted` for that direct
target only; it is not consumed and the same target resumes it in place. Only
the complete four-step prefix records `reconciled`, the one logical consumed
marker. If the source is still pending, the attempt is `blocked` and remains
retryable without claiming consumption. Its `target_source` must exactly equal
the current Trellis direct source `session:<target-key>`. The source rollout
`session_id` is provenance only and is rejected as target identity. Admission
never executes the pending action, starts a task, changes a task pointer, or
closes a task. A later, separately authorized continuation uses native Trellis
`task.py start` for an incomplete task and then rechecks its direct current
source. A completed task instead follows native Trellis finish/archive by
exact task path; do not manufacture a session pointer.

After a reconciled admission, `retention archive` atomically copies the core
and paired prompt after checking that the core is parseable and prompt is
readable. A retry after that archive is idempotent; a failed archive remains
archive-eligible and never repeats intake. `restore`, `reopen`, and
`purge` require the exact same handoff id confirmation. `purge` removes only
the canonical core/prompt after archive verification; it never deletes task,
rollout, session, memory, resource/watch, log, or remote data. The receipt is
kept as audit evidence. Run `status --handoff <core.json>` to inspect whether
the selected lifecycle mode is ready; the prompt renderer rejects a pending
high-assurance mode.

## New-Session Handoff Closure

The package has one logical consumption attempt for one direct target. In the
target session, “close the handoff” means reconcile the captured task with
current Trellis facts before resuming work:

1. Validate the exact package and stop unless the receipt is `ready`.
2. Read the paired JSON core and `session-handoff-prompt.md` completely before acting on its
   pending next action.
3. Run `$trellis-start` and compare the captured task, Git state, evidence,
   and pending action with current project facts. Record cumulative `admit`
   progress with `action_authorized=false`; only the complete read/start/
   reconciliation sequence becomes consumed.
4. If the captured task is now actually complete, use the normal
   `$trellis-finish-work` flow to finish and archive it before doing other work.
5. If it is incomplete, changed, or blocked, do not close it from the handoff
   snapshot; record the current disposition and use `$trellis-continue` only
   when continuing that task is appropriate.
6. Stop after this reconciliation. Do not execute the pending next action or
   begin new implementation until the user gives a subsequent instruction.

An incomplete read, timeout, network/model interruption, or process exit does
not become consumed. Once an `admitted` receipt exists, the same target resumes
that one attempt; a different target cannot replace it. After successful
admission, package retention archive is independent and may be retried without
consuming the asset again. Session-internal compaction and ordinary restart
only resume the target's current task and do not call handoff intake; a manual
post-compaction re-entry sees the completed target receipt as idempotent.

The package is a navigation hint. A `ready` receipt never proves that a task
is complete and never authorizes closing an unrelated current task. A source
rollout session id never binds the target Trellis task.

## Task Ownership Transfer

When the handoff contains a task, render the prompt, then advance the package
lifecycle and Trellis task ownership in this order. These orchestration
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

When the user also asks for the new-session entry prompt, render it once after
that exact `validate` reports `ready` to create the required paired prompt:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root> \
  --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

The renderer atomically creates the paired
`session-handoff-prompt.md` in the same timestamp directory. That first render
is source-side preparation, not delivery: retain its standard output while the
source runs `prepare`, required ownership `quiesce/seal`, `finalize`, and
`retire` as applicable. Confirm `status --handoff <core.json>` returns `ready`,
then rerun the renderer idempotently and return that standard output unchanged
as the final delivery, so the user can copy the `text` block directly into a
new Codex session. Do not append a summary, validation narration, or further
command after that final block.
The complete prompt directs the new session to validate again, then use the
normal `$trellis-start` flow, reconcile the captured task, and only then use
`$trellis-finish-work` or `$trellis-continue` according to current facts. Its
task and next action are navigation hints that never override current user
instructions, Trellis facts, Issue state, or Git state. After rendering a
ready-only prompt, stop; do not run `finish`/`archive` or any other mutation
that would invalidate the receipt. A later session can continue only after its
own validation and normal Trellis startup checks. The initial takeover stops
after reconciliation; it does not automatically execute the pending action.
