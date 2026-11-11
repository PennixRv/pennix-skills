# Pennix implementation order

1. Refresh current owner facts and preserve the immutable source archive required to uninstall the old private client after active code is removed.
2. Implement Cognee client/registration/launcher and focused tests using existing request/config helpers.
3. Replace handoff provider and lifecycle/routing references, then update static collection and integrity manifests.
4. Add the same-process recall ingress module and deployment handoff contract.
5. Run focused tests, full Python quality checks, source scans, and installed launcher smoke tests.
6. Commit, push `main`, stage through the native lifecycle, update the root project, and record non-sensitive receipts.

Do not copy credentials, database files, logs, or user runtime state into this repository or task.

## Implementation evidence (2026-10-04)

- Initial source commit 546d385 was incomplete against the sealed launcher/identity contract. Completed common-root registration, principal/service/dataset UUID binding and startup revalidation, native global disable and lifecycle-managed installed launcher, and explicit semantic governance commands.
- Live integration corrected API key authentication to the upstream X-Api-Key protocol; authenticated redirects fail closed. The shared native client lives in the memory owner, and handoff imports that single implementation.
- Native plugin add requires the root manifest in sparse checkout, normalizes the Git URL and enables the plugin. Adapter restores the previously disabled setting after that native call, verifies immutable marketplace ref and byte-identical installed plugin files, and preserves user configuration ownership.
- NAS non-root image permission regression fixed in reproducible overlays; official image version reports its documented -local suffix. No Cognee source/plugin fork or installed cache patch.
- Python CI files pass; final focused checks: lifecycle136, handoff27, memory5; compilation/diff checks pass. Grok native Node8 checks pass from its skill directory. Installed main/child/real-session/proof/governance acceptance remains pending in root task; do not close owner task yet.
