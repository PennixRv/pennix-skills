# Design

## Handoff

Use the current local JSONL lifecycle receipt and immutable core. Normalize
observation evidence once, then derive readiness from the selected mode. Keep
admission as a single successful target event: a blocked/incomplete attempt
does not consume the package; a reconciled attempt can be replayed safely by
the same direct target and cannot be replaced by another target.

Retention archive copies the core/prompt pair; ownership archive records task
control transfer. Neither is the same as an in-session compaction recovery.

## Retrieval

The default route performs the primary Grok request only. Extra sources are an
explicit opt-in (`--extra N`); when selected, the existing providers remain
bounded and observable. This keeps provider routing in the Pennix Skills layer
and does not move task or memory authority into the retrieval helper.

## Non-goals

No OpenViking/Trellis source change, no new database, no cryptographic package
gate, no arbitrary handoff size cap, and no new authorization subsystem.
