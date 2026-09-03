---
name: session-handoff
description: Create or validate a bounded Trellis session handoff after an explicit formal handoff request, or render its ready-only new-session entry prompt.
---

# Session Handoff

Do not use this Skill for ordinary work, restart, compaction, waiting, acceptance failure, provider failure, or a lost transport
handle. Those events do not authorize a handoff.

When the current user explicitly requests formal handoff, prepare a small request JSON outside the canonical destination and run:

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
Trellis facts, or Git state.
