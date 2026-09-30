# Pennix memory policy and handoff design

## Memory ownership and bank boundaries

The three banks are policy boundaries, not one shared pool:

| Layer | Bank / writer | Read/write rule |
| --- | --- | --- |
| Project, cross-session | Stable ID from the registered Trellis project; Hindsight Codex Stop hook is the only automatic writer | Opt-in project only; new session receives bounded recall; validate against current task/Git/files/spec |
| Cross-project knowledge | Explicit Pennix-managed bank | Main session may promote a verified, reusable conclusion with source project, evidence and applicability; never copy raw session transcripts |
| User memory | Private user bank | Write only on explicit request/confirmation of stable preference/fact; never auto-extract from project sessions |

Subnodes receive only the minimum context selected by the coordinator and do not get Hindsight tools/hooks. Project source files/specs remain authoritative. Hindsight pages/documents are derived copies with source/version; update or supersede them through explicit Pennix policy, never reverse-promote them automatically.

## Skill and routing boundary

Add one `pennix-hindsight-memory` skill for Pennix's ownership, three-bank policy, evidence/provenance, permission and promotion rules. The upstream Hindsight `hindsight-coding-agent` Skill remains the generic MCP/tool guide. Update `pennix-workflow-routing` and lifecycle inventory so OpenViking is not an active route. Avoid a broad second installer or duplicated Hindsight tool catalogue.

## Handoff state machine

Keep the existing local handoff package/core and Trellis ownership boundary. Replace only OV-specific parts. A normal handoff uses a stable document/operation identity derived from `handoff_id` and the registered project bank. Submit the semantic capsule through the authenticated v0.10.1 API, wait for synchronous completion if the locked server supports it or otherwise poll the returned operation ID to a terminal `completed`, then issue a bounded retrieval query and confirm that this handoff's document identity and metadata are retrievable. Semantic retrieval does not prove canonical content equality; the local capsule digest remains the content truth. If the association cannot be proved, retain local core and report `pending`/`blocked`.

The local runtime receipt records the handoff ID, bank ID, content hash, write mode, operation ID/status, retrieval status and timestamp—no transcript, capsule text or credential. Retrying the same handoff ID must not create a second logical write. A new ready receipt is produced only after retrieval verification. `core_only` is an explicit user-selected local path. `archive_required` and `convergence_required` are obsolete and return a clear unsupported-mode error; no compatibility checkpoint call remains. OV-shaped legacy core input is rejected with instructions to prepare a new package; no data is imported.

## API and safety boundaries

Use the official v0.10.1 authenticated API and the configured `apiUrl`/`apiToken` from the owner-managed Hindsight configuration; never print or serialize credentials. Do not route Pennix custom Handoff/tool operations through FastCtx. Limit requests to the named registered bank. Treat HTTP acceptance/operation queued, generic bank sync state, and knowledge-page existence as insufficient. Timeouts/retries use the same operation/document identity; failures are visible and cannot downgrade the default barrier.

## Validation

Deterministic tests use a fake HTTP server/client and temporary Trellis config/runtime receipts; no live Hindsight or real transcript is touched in unit tests. The parent integration phase additionally runs an isolated synthetic-bank canary against v0.10.1 for same-bank retain → terminal completion → same-document retrieval. If the locked public API cannot provide operation completion and same-document retrieval verification without changing Hindsight source, stop and return to the parent planning gate; do not substitute a weaker condition.
