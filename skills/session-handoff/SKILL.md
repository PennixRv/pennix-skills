---
name: session-handoff
description: Create or validate a bounded Trellis session handoff after an explicit formal handoff request, or render its ready-only new-session entry prompt.
---

# Session Handoff

The purpose of this Skill is to leave a bounded navigation record for a new
Codex coordinator session. It is not a transcript backup, task database,
checkpoint ledger, native session resume, or mechanism for continuing an
interrupted tool call. Trellis remains the source of truth for task and
lifecycle state; the new session must verify those facts again.

Do not use this Skill for ordinary work, restart, compaction, waiting, acceptance failure, provider failure, or a lost transport
handle. Those events do not authorize a handoff.

When the current user explicitly requests formal handoff, first finish and
verify the work that must be visible to the next session. Prepare a small
request JSON outside the canonical destination. Its exact top-level fields are:

```json
{
  "session_label": "short description of this session",
  "facts": ["verified fact with a stable project source"],
  "evidence_paths": ["AGENTS.md", ".trellis/workflow.md"],
  "next_action": "bounded next action for the new coordinator",
  "blockers": [],
  "risks": ["known residual risk"],
  "validation": [{"command": "check name", "result": "bounded result"}]
}
```

Paths must be project-relative, existing, non-runtime files. Do not put
credentials, raw tool output, transcript text, cache paths, or temporary
state in the request. Then run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/session-handoff/scripts/handoff.py" --project-root . \
  write --request <request.json> --explicit-user-request
```

The helper records only a bounded task/Git/evidence snapshot and requires the explicit flag. To inspect it later without writing:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/session-handoff/scripts/handoff.py" --project-root . validate
```

`ready` is a validation result, not authorization to implement. `changed`, `absent`, or `recovery_required` must be handled by
ordinary project fact verification. This Skill never changes task status, consumes a handoff, controls Trellis workers, or copies
conversation, credentials, cache, or runtime ledger.

When the user also asks for the new-session entry prompt, render it only after `validate` reports `ready`:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/session-handoff/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root>
```

The rendered prompt directs the new session to validate again, then use Trellis' normal `$trellis-start` and
`$trellis-continue` flow. Its task and next action are navigation hints that never override current user instructions,
Trellis facts, Issue state, or Git state. After rendering the ready-only prompt,
the current coordinator stops; it does not run a task archive/finish action
that would invalidate the receipt. A later session may continue only after its
own validation and normal Trellis startup checks.
