# Quality check

## Automated checks

- `python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p 'test_*.py' -v`
  — 70 tests passed.
- `bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh` — passed.
- `python3 -m py_compile skills/pennix-workflow-lifecycle/scripts/lifecycle.py
  skills/pennix-workflow-lifecycle/scripts/host.py
  skills/pennix-workflow-lifecycle/scripts/adapters/*.py` — passed.
- `git diff --check` — passed.

## Host evidence

Read-only `discover` on the current Arch/WSL2 host reports:

- Codex observed `0.154.0`, target/candidate `0.155.1`, owner `openai-codex-bin`.
- Trellis observed/target/candidate `0.6.41`, owner `@pennixrv/trellis`.
- FastCtx observed `0.2.6`, target/candidate `0.2.21`, actual owner `fastctx`,
  target owner `@pennixrv/fastctx`.
- AoE observed `1.13.2`, target/candidate `1.16.1`; the executable has no
  verifiable package owner and remains blocked rather than being removed.

The discover command remained read-only. No credentials, configuration bodies,
or runtime state were added to the task.
