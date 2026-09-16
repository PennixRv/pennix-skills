# OpenViking Handoff Source Observation Design

> **Superseded for implementation.** `checkpoint-decision.md` replaces this
> SessionEnd arm/finalizer design.

## Responsibility Boundary

`pennix-session-handoff` owns the intent, public-CLI observation, lifecycle
receipt, delivery prompt, and consumer receipt. The official OpenViking Plugin
owns all capture/catch-up/commit decisions. Codex owns the native SessionEnd
event. Trellis owns source pointer retirement and target claim. The design does
not add an OpenViking client protocol, inspect Plugin state, or recreate the
Plugin's rollout parser.

## Commands And Hook

```text
# source, while still directly bound to its task
handoff.py ... prepare --mode archive_required|convergence_required
handoff.py ... ownership quiesce ...
handoff.py ... ownership seal ...
handoff.py ... openviking-arm --handoff <core.json>

# called only by the reviewed SessionEnd Hook handler or explicit recovery;
# it reads the matching Hook-recorded witness for this exact handoff
handoff.py ... openviking-finalize --handoff <core.json>
```

`openviking-arm` verifies the prepared/sealed source and writes one private
runtime intent. It reads the deterministic `cx-*` session with `ov session get`
and saves only: handoff id/path, raw source session id, direct source context
key, selected lifecycle mode, canonical session URI, and numeric commit-count
baseline. The source core itself supplies the semantic capsule; no capsule hash,
text threshold, or second semantic validator is introduced.

The Hook handler receives native JSON on stdin, locates a Trellis root from its
`cwd`, derives the source context with Trellis' own `resolve_context_key` using
the event, and returns immediately unless one armed intent exactly matches the
raw session/context. On a match it atomically writes the native witness and
launches one detached finite finalizer. The fragment is shipped by Pennix but
merged into user `hooks.json` only through `codex-hook-registration`; Codex
`/hooks` trust is intentionally manual.

`openviking-finalize` performs bounded retry reads of the official CLI. It
first rejects a non-matching native witness/source context, then waits for
`commit_count > baseline`. The baseline is post-seal: a newer commit can be the
Plugin's documented SessionEnd catch-up or a threshold commit between arm and
source exit, and either covers B. The matching later native witness proves the
source did not continue beyond B; neither condition alone is sufficient. It
locates the newest archive and writes an atomic local observation. On verified
source state it calls the generic lifecycle `finalize`, then the existing
Trellis `ownership retire`, and finally the existing renderer. A
pending/unavailable outcome keeps the arm, witness if present, and source
ownership for one explicit recovery invocation.

## State Mapping

| Public/native result | Observation and lifecycle result |
| --- | --- |
| no matching native `SessionEnd` event | no worker, no observation |
| `ov` unavailable | `availability=unsupported` |
| CLI/server failure | `availability=unavailable` |
| session missing or `commit_count <= baseline` | available but archive/task/memory unverified; source remains pending |
| newer commit and newest archive exists | boundary/source/archive verified; `archive_verified` is eligible |
| same archive has `.done` | async extraction task `completed`, artifact is the `.done` URI |
| same archive also has `memory_diff.json` | memory verified; `converged` is eligible |

The source-session observation identity remains the raw original Codex id
because the lifecycle compares it with `source.rollout.session_id`. The derived
`cx-*`, canonical URI, archive URI, and `.done`/diff URIs are evidence details,
not Trellis identities. A missing `.done`/diff is never synthesized as an empty
successful result.

## Consumer Correction

`admit` remains the public command to avoid a second consumer protocol, but it
changes from cumulative partial progress to one atomic successful consumption:

1. fully parse/read canonical core and paired prompt;
2. require source lifecycle readiness and, for a task handoff, native ownership
   status `ready`;
3. require the target's direct identity, `$trellis-start`, and reconciliation
   attestation with all four ordered steps;
4. append `reconciled` once, or append nothing for incomplete/failed input.

Existing completed receipts remain readable and same-target calls are idempotent.
Partial legacy receipts remain interpretable for recovery, but new code does not
create an `admitted` consumer lock. Renderer and Skill text make target compact
or normal resume query the receipt and resume its current task rather than call
admission again.

Before this complete intake, a target that has one exact handoff path may run a
non-consuming readiness preflight. It stops pending if source lifecycle or
ownership is not ready. It may invoke the finalizer for recovery only when the
Hook already wrote the arm's matching native witness. There is no generic target
startup scan, and target identity/core/prompt cannot supply a source context or
source-end proof.

## Parsing, Writes, And Recovery

CLI calls use argument arrays, `stdin=DEVNULL`, a per-call timeout, and parse
the final JSON object when the known CLI command-echo prefix is present. They
do not retain raw stdout/stderr, credentials, configuration, or archive message
content. Runtime intent/observation files are project-relative under
`.trellis/.runtime/`, atomically written with `0600`; the immutable core and
prompt are never rewritten. There is one finite worker per explicit arm, no
scheduler or daemon. The Hook derives source context from its native event and
writes it only in the matching witness. A later recovery reuses it only after
matching arm, witness, and sealed ownership; it never asks a target to inject
environment variables or impersonate the source.
