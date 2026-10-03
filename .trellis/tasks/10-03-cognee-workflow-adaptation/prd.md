# Pennix Cognee workflow adaptation

Implement the authorized memory-base replacement in the Pennix owner repository. The real source of memory configuration, lifecycle, handoff, routing, and installed launcher behavior must use Cognee while preserving local Trellis/core authority and explicit opt-in project scope.

## Scope

- Add/replace the Pennix Cognee memory skill and native HTTP client.
- Add exact data proof, semantic record governance, improve flags, and the same-process SDK recall ingress used by the official API deployment.
- Replace active AgentMemory references in handoff, routing, lifecycle, configuration, tests, and static collection with Cognee; retain only historical migration evidence.
- Provide a managed `codex --no-daemon` launcher that enables Cognee only for registered projects and keeps unregistered/child sessions disabled.

## Acceptance

- [ ] Cognee client handles auth, dataset registration, exact raw reads, semantic writes, improve, correction/revoke/delete, and explicit core-only failure.
- [ ] Registration is canonical-root scoped and deterministic; no unregistered project writes to a shared dataset.
- [ ] Official capture remains the only automatic writer/injector; explicit Pennix records supplement it.
- [ ] Recall ingress forwards truth/global retriever flags without forking or monkeypatching Cognee and preserves native auth/ACL/DTO/SSE/error behavior.
- [ ] Active source/catalog/config/tests contain no AgentMemory implementation or fallback.
- [ ] Skill tests, lifecycle checks, and source collection/integrity checks pass; installed launcher and root project are exercised against the deployed service.

Root contract: ../../../../.trellis/tasks/10-03-cognee-memory-base-replacement.
