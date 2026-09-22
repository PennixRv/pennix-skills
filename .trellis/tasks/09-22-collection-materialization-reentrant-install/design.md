# Collection Materialization Design

## Ownership

The independent component repositories remain the writable source and release
owners. This repository carries read-only distribution snapshots under
`skills/<name>`, pinned in the sole lifecycle catalog.

## Delivery Contract

```text
source commit -> materialized collection directory -> catalog
             -> native Skill installer staging -> validate -> replace
```

The lifecycle orchestrates the native installer; it does not create a second
installer or a target-host checkout. It validates a complete staging tree before
replacing a known collection installation. Failure leaves the prior tree intact.

## Synchronization

A repository-owned workflow resolves each source default-branch SHA, materializes
the publishable files, updates the single catalog, and validates the result. It
opens or updates a PR only after all checks pass. Human merge remains the release
gate for `main`.

## Explicit Non-Goals

- No edits to component source repositories.
- No collection release tag or second version manifest.
- No global configuration or target-host deployment changes.
