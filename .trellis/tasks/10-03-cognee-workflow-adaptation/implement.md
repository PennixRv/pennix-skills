# Pennix implementation order

1. Refresh current owner facts and preserve the immutable source archive required to uninstall the old private client after active code is removed.
2. Implement Cognee client/registration/launcher and focused tests using existing request/config helpers.
3. Replace handoff provider and lifecycle/routing references, then update static collection and integrity manifests.
4. Add the same-process recall ingress module and deployment handoff contract.
5. Run focused tests, full Python quality checks, source scans, and installed launcher smoke tests.
6. Commit, push `main`, stage through the native lifecycle, update the root project, and record non-sensitive receipts.

Do not copy credentials, database files, logs, or user runtime state into this repository or task.
