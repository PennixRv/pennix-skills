# Trellis Beta Contract Evidence

Date: 2026-09-22

## Local integration contract

The root repository's `.trellis/spec/operations/workflow-governance-current.md` records the accepted Trellis fork as `@pennixrv/trellis@0.7.0-beta.7` and `@pennixrv/trellis-core@0.7.0-beta.7`, with the Pennix workflow using inline main-session execution and native Trellis task/channel ownership.

## Registry verification

Read-only npm checks returned:

- `npm view @pennixrv/trellis@0.7.0-beta.7 version --json` -> `0.7.0-beta.7`
- `npm view @pennixrv/trellis-core@0.7.0-beta.7 version --json` -> `0.7.0-beta.7`
- `npm view @pennixrv/trellis@0.7.0-beta.7 dist.tarball --json` -> `https://registry.npmjs.org/@pennixrv/trellis/-/trellis-0.7.0-beta.7.tgz`

The existing catalog target `0.6.43` is also present in npm, so the stale target is installable but does not satisfy the current integration contract.

## Product-source search

The direct `0.6.43` references are the catalog and `skills/pennix-workflow-lifecycle/tests/test_lifecycle.py`. Historical task artifacts contain superseded source-checkout and retired-protocol language; they are not product entry points and remain unchanged.
