# Implementation Plan

1. [x] Run the current handoff and retrieval tests and inspect the exact contract
   callers before editing.
2. [x] Trace and fix the source-readiness normalization at its shared contract
   boundary; add focused regression coverage for every affected mode.
3. [x] Verify admission replay and partial-consumption behavior; change only the
   smallest state transition necessary. A blocked intake remains retryable;
   only a reconciled admission advances retention to `archive_eligible`, and
   same-target replay is idempotent while another target is rejected.
4. [x] Align retrieval configuration, CLI defaults, and docs/tests so extras are
   explicit and sequential after Grok while the Grok-first route remains intact.
5. [x] Run Python/Node checks, inspect the diff and repository status, then commit
   and publish this independent component.

Validation before release:

- `python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py'` -> 20 passed.
- `npm test` in `skills/grok-search/` -> all source, proxy, response, output, retry and argv fixtures passed.
- `git diff --check` -> passed.
- Explicit extra fixture observed `/responses` before `/tavily/search`; default fixture observed only the Grok attempt.

Rollback: revert the component commit. Existing explicit `--extra` callers and
previous lifecycle receipts remain readable.
