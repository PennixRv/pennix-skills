# Implementation order

1. Run `trellis-before-dev` for the Skills/workflow and handoff backend layers. Read current Pennix skill contracts, task-owned specs, handoff schema/CLI tests, lifecycle catalog and the pinned Hindsight API/client source.
2. Implement the single `pennix-hindsight-memory` policy skill and adjust `pennix-workflow-routing`; remove OpenViking-only sections from active `pennix-worktime-memory`/handoff routes rather than retaining duplicate legacy instructions.
3. Update the handoff schema, validator, state/receipt functions and CLI. Remove the OV projection field/checkpoint module and retired modes; retain deterministic local core and explicit `core_only` behavior.
4. Add the minimal Hindsight handoff API adapter for the exact selected stable project bank. Reuse the API contract and any existing local HTTP helpers; do not add an SDK dependency, custom service, FastCtx wrapper, or Hindsight source fork. Store only minimal local operation/readback proof and ensure retry idempotence.
5. Update all affected Pennix active docs, route maps, tests and lifecycle Skill catalog/materialized collection list. Preserve archived task/research records as historical evidence.
6. Finish source implementation across this and the lifecycle/Trellis tasks before running tests. Then join the parent's unified test phase: Pennix full targeted suite, handoff fake-API contract matrix, lifecycle/Hindsight isolated integration and real synthetic-bank write/readback. Fix failures and rerun affected plus cross-boundary checks.
7. Commit/push Pennix `main`, publish any required repository release, reinstall the complete Pennix Skill set and run redacted lifecycle/handoff verification. Do not archive this owner task until its parent gates are recorded.

## Stop conditions

- Hindsight v0.10.1 does not provide a stable operation identity, terminal state and same-bank readback sufficient for exact `ready` proof.
- The project bank ID or API secret cannot be obtained from the official private client config without logging or weakening the owner-only permission boundary.
- A non-OV legacy handoff invariant would be broken by schema/mode removal.

On any stop, retain local handoff core and return evidence to the parent planning gate; do not silently change the ready guarantee or move policy into the root repository.
