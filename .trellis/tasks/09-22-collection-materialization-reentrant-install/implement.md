# Implementation and Locked Completion Plan

1. Complete and test owner releases on `main`: CCH `v0.1.41`, Grok `0.2.1`, and Windsurf `v0.1.16`; do not publish private/unavailable packages through an unverified channel.
2. Update lifecycle catalog/adapters for explicit configuration targets, private profile, collection receipt, closed post-install action IDs, exact source commits, and redacted discover/verify.
3. Materialize Grok from `29edb8f6f76bd048c436f921279a84db19c20bc0` and Windsurf from release commit `bc27fbf2dd04f9b8583193cc8b43a1e89ee37da1` npm-pack projection; verify no runtime metadata enters snapshots.
4. Update `pennix-decision-gates`, `pennix-fastctx-routing`, and `pennix-workflow-routing` contracts and tests: complex analysis routing, same-continuation persistence, final static-decision closure, owner-first native protocol exclusion, and Grok external ownership.
5. Make the sync workflow checkout catalog commits exactly, validate Grok runtime preparation, and retain PR-only publication behavior.
6. Run all source tests, structural checks, and release/package checks; inspect diff and `git diff --check`.
7. Commit and push this repository on `main`; reinstall via the native system skill installer using a sibling staging directory, run lifecycle `replace-staged`, then execute `discover` and `verify` and record the receipt/result.
8. Close/archive this owner task only after verification, update root task/session/workflow assets, and lock completion with no unresolved static decision or conditional acceptance item.

Locked completion conditions: owner commits/tags and collection catalog agree; all tests pass; live collection has a matching receipt; lifecycle discover/verify report no enabled-target or integrity failure; routing and decision-gate contracts pass; no credential value is present in Git, logs, task files, or output.
