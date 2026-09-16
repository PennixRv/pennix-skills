# OpenViking CLI Contract

> **Superseded decision basis.** The current CLI checkpoint findings are in
> `../checkpoint-decision.md`.

## Verified Commands

- `ov session get <cx-id> --output json --compact true` returns a `result`
  object containing `session_id`, canonical `uri`, `message_count`, and
  `commit_count`.
- `ov ls <session-uri>/history --limit 1 --sort-by mtime --sort-order desc
  --output json --compact true` returns the newest archive URI. The current
  CLI may prefix stdout with `cmd: ...`; the final JSON line remains the
  machine-readable result.
- `ov ls <archive-uri> --all --output json --compact true` exposes `.done` and
  `memory_diff.json` when asynchronous archive processing and memory
  extraction have finished.

## Official Semantics

`commit()` has synchronous archive creation and asynchronous summary/memory
extraction. A session archive is the source provenance; peer-scoped memories
are retrieved independently in later sessions. There is no supported active
session handoff/migration API.

## Integration Consequence

`ov session get` alone cannot prove a handoff source has ended: the Plugin may
make a threshold commit at Stop while Codex stays live. The arm takes its
baseline after B is sealed. The public proof combines a strictly newer
post-arm commit/archive with a matching later native Codex `SessionEnd` witness.
The newer commit may be the Plugin's documented end catch-up or a threshold
commit between arm and exit; both cover B, while only the witness closes the
source. Pennix relies on that published behavior rather than inspecting the
Plugin's marker/cursor/lock.

The CLI does not expose the Plugin's returned commit Task id to a separate
observer. For `convergence_required`, the finalizer instead uses the archive's
documented `.done` completion artifact and `memory_diff.json` extraction
artifact from the same post-end archive. It must report pending if either is
absent, not infer an empty memory diff.

Sources checked 2026-09-16:

- <https://docs.openviking.ai/en/api/05-sessions/llms.txt>
- <https://docs.openviking.ai/en/concepts/08-session>
- Installed Codex Plugin `DESIGN.md` and `session-state.mjs`.
- <https://developers.openai.com/codex/hooks.md>: matching hooks run
  concurrently and SessionEnd has a short synchronous deadline; checked
  2026-09-16.
