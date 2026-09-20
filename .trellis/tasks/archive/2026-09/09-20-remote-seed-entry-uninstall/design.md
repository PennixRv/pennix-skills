# Design: Remote Seed Bridge And Reversal

## Boundaries

Stage 0 is the remote Bash seed. It owns only the initial Codex package and
the two fresh static files it writes. `pennix-workflow-lifecycle` remains the
only user-facing owner of full collection, static extension, package, plugin,
and project lifecycle actions.

## First-Session Bridge

The seed prints one exact first-session request for the built-in
`$skill-installer`. It names the public repository and only the
`pennix-workflow-lifecycle` path. That turn ends after bridge installation,
because Codex exposes an installed Skill no earlier than the next turn.

The lifecycle Skill then directs the subsequent turn to make a clean explicit
source checkout and use it to install the collection. This keeps the seed from
cloning or executing the full remote Pennix source, and keeps checkout/ref
choice explicit.

The bridge is initially installed directly under the host skills root, while
the collection installs it beneath `pennix-skills/`. Before collection
replacement, the installer compares the standalone bridge to the source
recursively, ignoring only Python bytecode caches. A match is removed after
the collection is available; a mismatch blocks before replacing the managed
collection.

## Reversal Boundary

Stage 0 does not offer a reversal mode. It is deliberately a minimal initial
installation writer, while `pennix-workflow-lifecycle` already has exact
component and native-owner uninstall contracts. Reimplementing that behavior
in seed would either duplicate those contracts or risk deleting credentials,
AUR helpers, build dependencies, and later workflow assets without provable
ownership.

The bridge instruction must state that full workflow removal begins only after
the lifecycle bridge and collection are installed, then uses one explicit
component uninstall at a time.
