---
name: pennix-session-handoff
description: Create, validate, or render one explicit, timestamped Pennix session handoff package with a bounded local Codex rollout projection. Use only for a current user-requested formal cross-session handoff.
---

# Pennix Session Handoff

This Skill creates a bounded navigation package for a new Codex coordinator
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
  "next_action": "bounded next action for the new coordinator",
  "blockers": [],
  "risks": ["known residual risk"],
  "validation": [{"command": "check name", "result": "bounded result"}],
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
may be large; the projected candidates, timeline, metadata, and individual
records remain bounded. It excludes
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
package. It records a task snapshot, bounded Git history, content digests for
the requested evidence, and a rollout coverage/candidate projection. It does
not upload rollout content or call external models.

To inspect one package later without writing, use the exact emitted path:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" \
  --project-root . validate --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

Appending after the captured rollout boundary remains valid. Modifying,
truncating, replacing or losing the captured prefix, changing the task/Git
snapshot, or changing a requested evidence file invalidates the receipt.
`ready` is a validation result, not authorization to implement. `changed`,
`absent`, or `recovery_required` must be handled by ordinary project-fact
verification. This Skill never changes task status, consumes a handoff,
controls Trellis workers, or copies a conversation, credential, cache, or
runtime ledger.

## New-Session Handoff Closure

The package has no independent consumed or closed state. In a new session,
“close the handoff” means reconcile the captured task with current Trellis
facts before resuming work:

1. Validate the exact package and stop unless the receipt is `ready`.
2. Run `$trellis-start` and re-read the current task, Git state, and acceptance
   evidence.
3. If the captured task is now actually complete, use the normal
   `$trellis-finish-work` flow to finish and archive it before doing other work.
4. If it is incomplete, changed, or blocked, do not close it from the handoff
   snapshot; record the current disposition and use `$trellis-continue` only
   when continuing that task is appropriate.

The package is a navigation hint. A `ready` receipt never proves that a task
is complete and never authorizes closing an unrelated current task.

When the user also asks for the new-session entry prompt, render it only after
that exact `validate` reports `ready`:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root> \
  --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

The renderer atomically creates the paired
`session-handoff-prompt.md` in the same timestamp directory. Standard output
contains only the short new-session entry index, not the complete handoff.
The complete prompt directs the new session to validate again, then use the
normal `$trellis-start` flow, reconcile the captured task, and only then use
`$trellis-finish-work` or `$trellis-continue` according to current facts. Its
task and next action are navigation hints that never override current user
instructions, Trellis facts, Issue state, or Git state. After rendering a
ready-only prompt, stop; do not run `finish`/`archive` or any other mutation
that would invalidate the receipt. A later session can continue only after its
own validation and normal Trellis startup checks.
