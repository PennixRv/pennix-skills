# Lifecycle fresh-environment convergence

## Goal

Make `pennix-workflow-lifecycle` a reproducible lifecycle entry for the
supported Arch Linux hosts (native Arch and Arch Linux under WSL2). The source
checkout remains the only implementation authority and
`references/component-versions.json` remains the only version/ref catalog.

## Required behavior

- `discover` is read-only and reports the catalog target, observed version,
  observed package owner, safe package candidate, and status.
- Version parsing must use the actual final version emitted by a command, even
  when an update notice appears before it.
- A catalog-declared package replacement (including scoped npm migration) is
  explicit and safe: the old owner is removed through its native package owner,
  the new owner is installed, and an unmanaged PATH shadow blocks instead of
  being deleted.
- `configure` is a supported lifecycle action and follows the existing
  idempotent static-template rules; unsupported native-owner configuration
  remains blocked rather than guessed.
- `install`, `upgrade`, and `uninstall` keep current fail-closed behavior and
  verify postconditions through a fresh probe.
- Catalog values are updated only from verified current package/ref evidence;
  no second version table or automatic latest-writer is introduced.

## Acceptance

- Existing tests plus regression tests cover final-version parsing, npm owner
  detection/replacement, package candidate reporting, configure dispatch, and
  unmanaged PATH shadow protection.
- Source tests pass and the collection can be installed from this clean source
  checkout without changing the installed copy into a second authority.
- The root task records source commit, push/install evidence, and any local
  component upgrades or protected drift that remain unmodified.
