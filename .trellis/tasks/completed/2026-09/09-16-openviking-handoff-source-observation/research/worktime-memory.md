# Worktime Memory

> **Superseded decision.** The current worktime conclusion is in
> `../checkpoint-decision.md`.

## 2026-09-16: Source witness and target recovery boundary

- Arm occurs after B is sealed. `commit_count > arm baseline` proves an archive
  after B; it may result from Plugin end catch-up or a post-arm threshold commit
  before exit. The matching later native SessionEnd witness separately proves
  the source closed at the formal boundary.
- The Hook is the primary source finalizer. Exact-path target preflight is
  non-consuming and may recover only from an already recorded matching witness.
  Target identity, core, and prompt are never source authority.
- Keep the implementation limited to one finite worker, public `ov` CLI reads,
  existing Trellis ownership operations, and Pennix receipts. Do not introduce
  a scheduler, generic SessionStart Hook, Plugin-private reads, or session
  migration.

Sources: official OpenViking session and Codex Hook documentation checked
2026-09-16; detailed evidence is in `openviking-cli-contract.md` and the
implementation contract is in `design.md`.
