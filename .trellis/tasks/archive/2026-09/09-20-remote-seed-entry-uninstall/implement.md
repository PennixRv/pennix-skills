# Implementation Plan: Remote Seed Bridge And Reversal

1. Update the seed completion output and lifecycle/README instructions with the
   two-turn bridge contract and lifecycle-only uninstall boundary.
2. Extend `test_seed.py` for the exact first-session bridge output and retain
   the existing no-unannounced-deletion contract; adjust documentation tests
   only as required by the final design.
3. Run focused tests, source collection validation, and the relevant workflow
   integration check. Review the full diff before proposing the scoped commit.
