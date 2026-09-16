# Authoritative Implementation Decision: OpenViking Checkpoint

This document supersedes the earlier SessionEnd arm/finalizer proposal. Pennix
must not install a SessionEnd Hook for formal handoff.

## Component Contract

Add `openviking-checkpoint --handoff <core>` and its status/recovery path to
`pennix-session-handoff`. The command operates while source ownership is sealed
but still directly active. It uses only `ov` argument-array invocations:

1. derive documented source `cx-<safe-codex-session-id>`;
2. atomically record checkpoint intent under `.trellis/.runtime/`;
3. append one assistant message containing an ordinary exact `handoff_id` marker
   and the verbatim Semantic Handoff Capsule;
4. invoke `ov session commit <cx-id>` and parse the actual returned JSON;
5. verify the response is an archived expected source URI and public grep/read
   finds the marker in that archive;
6. map the response's exact archive/task to generic lifecycle observation;
7. for convergence, read only `ov task status <returned-task-id>` and exact
   archive `.done`/`memory_diff.json` before lifecycle success.

The command never accesses a rollout path, Plugin state/cursor/marker/lock,
HTTP endpoint, or raw transcript. Direct commit archives server-live messages;
the formal checkpoint covers semantic B even when the current Codex turn has not
yet been captured by Plugin Stop. Plugin Stop/PreCompact/SessionEnd continue to
capture actual rollout content later.

## Receipt and Recovery

Persist small atomic stages for pending append, actual commit response, verified
marker/archive and task state. If a remote request outcome is uncertain, retain
`pending`; search only the exact source session for the handoff marker. Reuse a
located archive, or issue a new labeled checkpoint only when absent. No invented
success, checksum, content cap, or target reservation.

Do not build a polling service. An explicit foreground wait can poll the one
commit-returned task; normal status returns `pending` when it is not terminal.
Do not use global `ov wait` as task evidence.

Renderer delivery and `admit` require both Pennix lifecycle readiness and
Trellis sealed-handoff escrow readiness. `admit` continues to atomically record
only a complete target read/start/reconciliation. Resume reads the completed
receipt and does not re-admit.

## Trellis Call Boundary

Pennix invokes the new Trellis `retire-handoff <handoff-id>` only after its own
checkpoint evidence is ready. It never passes an old source context id into a
target environment. Recovery uses the same exact core and runtime receipt, then
the same idempotent retirement operation.

## Tests

Cover normal archive, exact marker, asynchronous convergence, no-op commit,
unavailable CLI, response ambiguity, marker absent/present recovery, no private
Plugin access, source/target readiness gates, partial consumer intake,
compaction/resume and exact-once competing target behavior. Keep existing
core-only and legacy receipt tests green.
