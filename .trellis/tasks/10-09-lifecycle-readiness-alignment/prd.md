# Align AoE baseline and SiYuan helper readiness

## Goal and admission

Close the two full-verification failures verified by the root coordination task
`10-09-grok-windsurf-fastctx-upgrade-plan`, revision 3. This is direct,
change-bearing work within the existing lifecycle owner, with a bounded change
and immediate regression path. Start only after the root's revision 3 has been
sealed, presented and subsequently approved. No independent planned-source
approval record is manufactured from the parent's approval.

## Requirements

- Change the single catalog AoE approved version from 1.18.0 to the officially
  released, already installed 1.19.0. Keep its pinned policy and AUR package owner.
- In `scripts/adapters/siyuan.py`, accept a managed helper command only when its
  two parsed argv items are the exact installed helper path and an absolute
  interpreter path proven by filesystem samefile to be the expected executable.
  Preserve every other parsed field, marker and exact managed stanza check.
- For the proven alias comparison, reuse the existing section generator with
  the observed helper string. Normal configuration generation remains native.
- Do not write, rotate or copy the real connection/token/config; do not change
  NAS, MCP transport, notebooks or knowledge behavior.
- Add positive and negative cases in `test_siyuan_connection.py`, and document
  the bounded integrity contract in the existing quality spec.

## Acceptance Criteria

- [ ] Same-file absolute interpreter aliases pass readiness; configuration and
  private record bytes remain unchanged, with no terminal input.
- [ ] A different interpreter, a changed helper path, extra argv, a missing or
  unverifiable executable, required-field drift and marker drift fail closed.
- [ ] The existing lifecycle/configuration/install suite, routing contracts,
  syntax and diff checks pass.
- [ ] Commit and push this source to main; the parent installs the complete
  collection through the native installer/lifecycle and records the exact SHA.
- [ ] The parent's native AoE verification matches 1.19.0, SiYuan readiness is
  configured, full verify has no corresponding failures, and offline integration
  passes. Temporary fixture/staging artifacts are cleaned by their owners.

## Verified basis and rollback

The installed native SiYuan MCP returns 3.8.6. Only the helper interpreter's
string differs: /usr/sbin/python3 and /usr/bin/python3 are the same file. AoE
1.19.0 is installed through agent-of-empires-bin and has an official non-draft,
non-prerelease upstream release. Detailed evidence stays in the parent research
record; no secret or runtime output is copied here.

The parent rolls the collection back through the existing native owner to a
verified source/receipt if needed. No private record or user config is changed
by this fix; an old collection may resume its false blocked diagnosis, without
changing the server connection itself.
