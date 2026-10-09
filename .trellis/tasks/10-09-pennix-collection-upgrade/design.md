# Design

## Ownership and data flow

The Pennix repository is the source of truth. The system Skill installer
creates a complete temporary sibling staging collection. Lifecycle validates
the exact catalog set, materialized source snapshots, package dependencies and
Grok dispatcher, then atomically swaps the collection, receipt and managed
command links. The receipt is the only authority for later link removal.

`catalog → staged collection → validated command mapping → atomic collection /
receipt / link replacement → discover and verify`.

Configuration state remains owned by the lifecycle adapter. It may inspect
only the private lifecycle-marked record shape, performs safe atomic updates,
and never prints or copies secrets. Profile migration removes only the exact
retired target and recomputes the current catalog digest. Unknown, malformed,
public, symlinked or ambiguous records block.

Windsurf uses the same validated collection resolver for `config-doctor` and
`configure`: collection member → expected native command path → safety and
ownership checks → native owner invocation. PATH is only an output/diagnostic
surface, never the resolver.

## Receipt and command contract

Schema 2 preserves the tree digest and adds a finite command map. Each mapping
contains the command name and collection-relative target, with no arbitrary
absolute path. The target must be a regular executable inside the exact live
collection; the destination must be absent or a receipt-matched managed link.
Schema 1 remains readable only for an explicit `replace-staged --yes`, which
atomically upgrades it to schema 2. Discover reports link drift and PATH
shadowing; replace and uninstall fail closed on unowned content.

## Firecrawl retirement

The catalog drops the Firecrawl configuration target and active adapter path.
The state adapter keeps a narrow migration branch for a lifecycle-marked
Grok record, exact old profile target, and exact old cooldown file. It removes
only those proven fields/records and preserves provider credentials, Tavily,
other targets, run records and unrelated cache. No broad recursive cleanup is
allowed.

## Out of scope

No Trellis source or project assets, no CCH changes, no FastCtx version or
server changes, no Windsurf runtime release, no user shell/profile edit, no
new global installer, no new secrets, and no active Firecrawl capability.
