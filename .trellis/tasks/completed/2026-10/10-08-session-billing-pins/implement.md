# Execution Plan v1

Planning until this task's own sealed revision is explicitly approved in the bundle. Native approve/start, main only, main-thread implementation and verification.

1. After paired Trellis and CCH official release checks pass, update catalog pins and lifecycle deployment/verification references.
2. Run python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests and git diff --check. No tests mirroring a version-string change.
3. Commit/push main and record immutable install SHA. Root completes project/system updates through their native owners.
4. Use system skill-installer/git from that SHA to stage the full catalog collection, verify integrity and executable bits, then native replace-staged. Verify installed source/provenance and scoped owner results.
5. Record unchanged config/secret hashes only, never values. Clean registered staging/backup/candidate files only after success; preserve durable relation metadata.
6. Commit owner verification, native archive/journal after root integration.

Any release mismatch, source-integrity failure or unresolved user customization conflict blocks completion; do not overwrite or fake receipts. Material owner/risk/behavior changes return to planning.
