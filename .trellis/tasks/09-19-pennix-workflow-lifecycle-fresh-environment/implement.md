# Implementation plan

1. [x] Activate this source task after the PRD/design are present.
2. [x] Inspect and patch the shared lifecycle probe, candidate, owner-migration,
   configure dispatch, and catalog paths.
3. [x] Add focused regression tests and update the lifecycle Skill wording.
4. [x] Run the lifecycle unit suite, shell syntax checks, and a read-only discover
   against the current host.
5. [x] Commit and push the source branch; install the resulting collection through
   the lifecycle adapter.
6. [x] Upgrade only verified package-owned local components; preserve protected
   user configuration and unmanaged files, and record that evidence in the
   root task.
