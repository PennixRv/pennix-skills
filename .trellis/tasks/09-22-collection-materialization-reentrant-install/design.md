# Workflow Governance and Lifecycle Design

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

## Configuration

The lifecycle catalog declares a finite target list. `codex-provider` is core;
optional owner targets are enabled only after an explicit target configure
action. Values enter through owner-native `/dev/tty` or owner UI, are written by
the owner adapter to private files, and never enter `.env`, argv, task files,
inventory, or chat. `CODEX_HOME/pennix-workflow-lifecycle/profile.json` stores
only selected target IDs plus a normalized configuration-contract digest. A
receipt beside the installed collection stores only its tree digest and is
required for full collection replacement/removal.

## Routing and Planning

Complexity is independent from `analysis_only`: cross-owner research and
governance work remains a Trellis planning task. Decision gates persist same-turn
answers before recalculating dependent nodes, and final seal rejects all static
TBD/TODO/decision-needed points. FastCtx is ordinary local-operation plumbing;
Trellis task/Channel, session handoff, native Codex interaction, Hook/MCP/TUI,
owner retrieval, and lifecycle protocols remain on their native owners.

## Synchronization

A repository-owned workflow materializes the exact catalog commit, validates the
publishable files and the Grok runtime action, and opens or updates a PR only
after all checks pass. Human merge remains the release gate for `main`; it never
rewrites the catalog to a moving branch head.

## Explicit Non-Goals

- No edits to component source repositories.
- No collection release tag or second version manifest.
- No shared `.env`, secret synchronization, or target-host credential copy.
