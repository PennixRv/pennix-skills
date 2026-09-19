# Quality check

## Automated checks

- `python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p 'test_*.py' -v`
  — 71 tests passed.
- `bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh` — passed.
- `python3 -m py_compile skills/pennix-workflow-lifecycle/scripts/lifecycle.py
  skills/pennix-workflow-lifecycle/scripts/host.py
  skills/pennix-workflow-lifecycle/scripts/adapters/*.py` — passed.
- `git diff --check` — passed.
- Package installs/removals pass `--noconfirm` for pacman/yay/paru, so an
  explicit lifecycle `--yes` cannot hang on the AUR clean-build prompt.

## Host evidence

Read-only `discover` on the current Arch/WSL2 host reports:

- Codex observed/target/candidate `0.155.1`, owner `openai-codex-bin`.
- Trellis observed/target/candidate `0.6.41`, owner `@pennixrv/trellis`.
- FastCtx observed/target/candidate `0.2.21`, owner `@pennixrv/fastctx`; the
  declared old `fastctx` owner was removed.
- AoE observed/target/candidate `1.16.1`, owner `agent-of-empires-bin`; the old
  unmanaged executable remains recoverable at
  `/home/penn/bin/aoe.pre-pennix-1.13.2`.
- CodeGraph, OpenViking, Ponytail, CCH, Hikari, and tmux also match catalog
  targets.

`verify` returns `2` only for the intentionally protected, user-maintained
`CODEX_HOME/config.toml` and `CODEX_HOME/AGENTS.md` drift. It reports no
package, plugin, source, or upstream-inspection failure.

The discover command remained read-only. No credentials, configuration bodies,
or runtime state were added to the task.
