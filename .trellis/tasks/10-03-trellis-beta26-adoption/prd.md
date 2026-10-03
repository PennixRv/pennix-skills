# Adopt Trellis beta.26 lifecycle pin and consumer assets

## Goal

Pin the released CLI/core beta.26 in the single catalog, reinstall the exact Skills collection and adopt native bundled project assets.

## Requirements

- Root coordinator 10-02-trellis-subnode-terminal-wait authorizes the exact beta.26 pin, native Skills staging/replacement, global CLI upgrade and native project adoption. This owner remains main.
- Change only the single lifecycle catalog pin and its existing contract assertion. No new installer, retrieval API, configuration or dependency.
- Seal: fixed source/native update path; catalog-only installer paths from an immutable pushed commit, then lifecycle replace-staged and trellis-cli upgrade. Preserve native workflow choice and all local state. Root records seven-consumer integration.

## Acceptance Criteria

- [ ] Catalog and existing lifecycle tests agree on beta.26; source is committed and pushed.
- [ ] Exact collection replacement and scoped verification pass; global CLI/core beta.26 are public and installed.
- [ ] Native project update preserves workflow choices and receipts; owner task and journal are closed and pushed.

## Notes

- Lightweight catalog/adoption task, PRD-only seal closed 2026-10-03. Release source fafcdd32, tag commit 32fb739c. Public visibility is checked before installation.
