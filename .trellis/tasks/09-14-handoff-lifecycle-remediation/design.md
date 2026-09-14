# Handoff Lifecycle Design

## Boundaries

The immutable handoff JSON and paired prompt retain the captured task scene and
semantic capsule. Trellis retains task ownership and current-session recovery.
OpenViking remains semantic-memory infrastructure. The local lifecycle JSONL is
only the existing per-handoff coordination receipt.

## Source Readiness

`prepare` fixes the selected proof mode. The renderer writes the immutable
paired prompt before `finalize`. `finalize` verifies the core, prompt and
observation, then records the selected source state. Target admission cannot
turn a pending source into ready.

## Consumption Attempt

The target axis already has the required state shape:

```text
not_admitted -> admitted -> reconciled -> disposed
```

`admitted` now means one direct target has a partial intake attempt. Its
progress is stored in the existing append-only event's evidence references as
an ordered `steps=` projection beside the existing `target=` reference:

```text
core_read -> prompt_read -> trellis_started -> facts_reconciled
```

The first incomplete prefix writes `admitted`; later calls by the same target
advance that prefix. A completed prefix transitions to `reconciled`, the sole
logical consumed marker, and makes retention archive eligible. A different
target is refused after either `admitted` or `reconciled`. Exact re-entry is
idempotent. This keeps schema-v2 receipts readable and avoids a parallel state
store or new trust mechanism.

## Archive And Compaction

Retention archive runs only after `reconciled` and atomically copies the core
and prompt using the existing code. A failed archive leaves the receipt
archive-eligible; an already archived retry is idempotent. It neither repeats
admission nor closes a task. Normal compaction uses Trellis's live-session
state and has no call path into `admit`; a post-compaction re-entry merely sees
the same target's idempotent completed receipt.

## Compatibility And Rollback

Existing receipt schema-v2 events remain readable. New target attestations add
the explicit `core_read` step; they do not claim that a local script can prove
model comprehension. Roll back by reverting the source commit and reinstalling
the prior published Pennix Skills revision; never patch the installed copy.
