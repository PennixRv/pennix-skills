# Implementation Plan

1. Activate this component task after reviewing these artifacts.
2. Run a product-source-only search for stale Trellis targets, retired protocol names and source-checkout deployment instructions.
3. Update the catalog target and direct lifecycle test expectation if the verified package metadata remains valid.
4. Fix only additional reproduced compatibility defects; otherwise record a no-change disposition for each reviewed Skill.
5. Run validation:

   ```bash
   bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh
   python3 -m compileall -q skills
   find skills -path '*/tests/test_*.py' -type f -print0 | sort -z | xargs -0 -n1 python3
   git diff --check
   ```

6. Review the diff, commit the component changes, push `main`, publish only under the repository's established release contract, and verify the published artifact/catalog.
7. Record commit, release and validation evidence in this task; the root coordinator will record integration acceptance separately.

## Explicit Non-Goals

Do not change Trellis source, user Codex configuration, credentials, plugin state, project assets, historical tasks, or unrelated branches.
