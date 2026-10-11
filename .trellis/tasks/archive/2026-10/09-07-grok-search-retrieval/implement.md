# Implementation

1. Copy the complete upstream package at the recorded commit into the direct
   Skill directory, excluding source-control metadata and generated modules.
2. Apply the two local compatibility changes: default extra count one and
   Pennix-specific Skill instructions/metadata plus upstream provenance.
3. Make the existing atomic installer run `npm ci --omit=dev --ignore-scripts`
   in the staged `grok-search` directory; test both its invocation and its
   pre-replacement failure behavior.
4. Update the two existing retrieval routing Skills without duplicating the
   upstream command reference.
5. Run upstream offline tests, Python installer tests, Skill validation,
   installer `--check`, then a disposable install target. Review the staged
   dependency and no-secret boundaries.
6. Commit and push only this repository's source/task files. The root task
   later records the resulting commit and runs the explicit user-level install.
