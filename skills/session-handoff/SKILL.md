---
name: session-handoff
description: Create or validate the bounded Trellis session handoff only after the current user explicitly requests formal cross-session handoff.
---

# Session Handoff

Do not use this Skill for ordinary work, restart, compaction, waiting, acceptance failure, provider failure, or a lost transport
handle. Those events do not authorize a handoff.

When the current user explicitly requests formal handoff, prepare a small request JSON outside the canonical destination and run:

```bash
python3 .agents/skills/session-handoff/scripts/handoff.py --project-root . \
  write --request <request.json> --explicit-user-request
```

The helper records only a bounded task/Git/evidence snapshot and requires the explicit flag. To inspect it later without writing:

```bash
python3 .agents/skills/session-handoff/scripts/handoff.py --project-root . validate
```

`ready` is a validation result, not authorization to implement. `changed`, `absent`, or `recovery_required` must be handled by
ordinary project fact verification. This Skill never changes task status, consumes a handoff, controls Trellis workers, or copies
conversation, credentials, cache, or runtime ledger.
