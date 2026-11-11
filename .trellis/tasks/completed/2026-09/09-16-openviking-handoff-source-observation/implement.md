# Execution Plan

> **Superseded for implementation.** Follow `checkpoint-decision.md`; do not
> install the SessionEnd Hook or implement its finalizer path below.

1. Add small `ov` JSON read helpers, source-arm runtime intent, native-witness
   recording, and the finite post-arm SessionEnd finalizer to `handoff.py`;
   reuse the existing generic observation/lifecycle/ownership/render helpers.
2. Add a Pennix-owned native SessionEnd Hook handler and reviewed hook fragment.
   The handler must be a no-op for absent/mismatched intents and must detach the
   finalizer before Codex's short SessionEnd Hook deadline.
3. Adjust renderer and `admit` gates: require retired/ready ownership before
   delivery; provide exact-path pending preflight and witness-only recovery;
   read full assets and record only complete successful admission.
4. Test with a fake `ov` executable and fake/native event fixture: isolated
   threshold commit rejection, post-arm threshold commit plus end-witness
   success, successful end catch-up archive, incomplete convergence, unavailable
   CLI, witness-only worker recovery, no `ov session commit`, pending target
   preflight, partial target, successful target, competing target, and resume
   idempotence.
5. Document command ordering, SessionEnd/Plugin responsibility, non-migration,
   recovery, Hook trust, and compact-versus-handoff distinction in the handoff
   and routing Skills.
6. Run the full handoff and hook-registration suites, inspect the diff, commit,
   push, publish/reinstall, validate/merge the reviewed fragment, and perform
   a read-only installed smoke check.
