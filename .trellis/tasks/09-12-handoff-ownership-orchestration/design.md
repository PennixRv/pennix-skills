# Design

`pennix-session-handoff` remains the immutable core package producer and validator. The ownership-aware
layer is an orchestration adapter around native Trellis commands:

```text
prepare source -> Trellis ownership quiesce/retire -> core ready
target validate/read/start/reconcile -> explicit claim -> consume -> retention archive
```

The adapter never writes `.trellis` task pointers and never treats OpenViking recall, Plugin capture, or a
handoff prompt as authorization. It passes exact handoff/core digests and current session identity to Trellis,
then records only the bounded result. Missing or unsupported OpenViking receipt keeps the semantic gate withheld
while control-only handoff remains available.

The lifecycle sidecar is append-only and external to the immutable package. Event identity is derived from the
exact handoff, state, actor, generation, and request digest, making repeated commands idempotent. The package is
never marked consumed or closed, and retention purge is exact-path, copy-first, and unrelated to Trellis task or
OpenViking data deletion.
