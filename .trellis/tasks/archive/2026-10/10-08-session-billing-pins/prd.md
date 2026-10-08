# Session Billing Release Consumption

## Goal

Consume the verified Trellis and CCH fixes from root task 10-08-session-child-billing, through correct deployment owners and every related landing point.

## Requirements and acceptance

- Pin only actual officially published/verified paired Trellis version and CCH GitHub Release version in the lifecycle component catalog.
- Explain relation metadata retention, recorder activation/old-history exclusion, system upgrade versus project update, and real-entry verification.
- Preserve CCH native-owner installation/upgrades; lifecycle performs only its supported scoped verification for CCH.
- Install the complete skill collection from an immutable source commit via the existing native staged installer and verify permissions/provenance.
- Root coordinates both CCH global copies/managed runtime, seven initialized project consumers and user ~/.codex managed assets; no residual obsolete installed copy for these components.
- Pass existing lifecycle tests, commit/push source and verify installed collection with the final catalog.

## Boundary

This independent repository's main is the source writer. No new Skill/router/database/session store, no prior-history importer, no Marketplace release and no unrelated component deployment. Root stores coordination evidence only. Planning approval is not implementation permission.
