# Implementation Plan

1. Replace the two gitlinks with source-SHA-pinned ordinary Skill snapshots and
   remove their `.gitmodules` entries.
2. Simplify the catalog and lifecycle paths to one collection source; implement
   staging validation and atomic replacement using existing lifecycle helpers.
3. Add the collection sync workflow plus structural, lifecycle, and regression
   tests; update repository and Skill documentation.
4. Run full collection tests and structural checks, commit/push `main`, then
   reinstall through the native installer and verify the catalog entry set.
