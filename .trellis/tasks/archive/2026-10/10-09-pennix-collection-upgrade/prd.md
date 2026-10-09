# Pennix collection consumer upgrade

## Problem

The approved three-component upgrade has produced a released private
`grok-search` v0.3.0, while the Pennix collection still points at the old
Grok snapshot, exposes a retired Firecrawl target, resolves Windsurf through
an arbitrary PATH command, and records only a tree digest for collection
ownership. The routing Skills also need a precise contract for distinguishing
the host's native FastCtx tool surface from the nested `functions.exec`
inventory.

## Scope

Update this independent `pennix-skills` source repository and its tests so the
collection can safely consume the approved Grok release and existing Windsurf
consumer artifact. Extend the existing lifecycle transaction and receipt with
the minimum command ownership needed for the lifecycle-managed
`~/.local/bin/grok-search` entry. Remove the active Firecrawl configuration
target and adapter while retaining only safe, owner-controlled migration
recognition. Resolve Windsurf `configure` and `config-doctor` through the
verified collection member. Add the two approved routing contract clarifications
and tests.

Do not modify Trellis, CCH, FastCtx server/configuration/binaries, user
secrets, or unrelated installed files. Do not create a generic installer,
global npm package, shared secret store, or a second routing layer.

## Acceptance criteria

- Catalog points Grok at the released v0.3.0 source commit/archive and points
  Windsurf at its verified 0.1.16 consumer provenance; the catalog contains no
  active Firecrawl target or adapter.
- Collection receipt schema 2 records only validated, lifecycle-owned command
  mappings; schema 1 can be migrated only through explicit transactional
  replacement. `discover`, `verify`, `replace-staged`, upgrade, uninstall and
  rollback protect unknown files, links, ancestors, PATH shadowing and other
  CODEX_HOME ownership.
- `~/.local/bin/grok-search` is created, verified, replaced and removed only
  when the receipt proves the exact collection target; no unowned same-name
  file or link is overwritten.
- Firecrawl migration recognizes only safe lifecycle-owned state and removes
  only the precise retired target/field/cooldown record while retaining other
  configuration and profile targets; unsafe or ambiguous state blocks.
- Windsurf lifecycle configuration uses the verified collection entry for both
  `config-doctor` and `configure`, never an arbitrary PATH executable and
  never by reading or copying its credential.
- Routing Skills and their existing contract tests state that `ALL_TOOLS` is
  not the native host inventory and that exposed native FastCtx errors retain
  their original classification.
- Existing lifecycle, configuration, install and routing tests pass; source
  changes are committed and pushed on `main`.
