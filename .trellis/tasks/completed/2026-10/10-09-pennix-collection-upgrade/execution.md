# Execution and acceptance

The task's revision 1 was sealed, then explicitly approved through the host's
blocking question and started through the native task CLI. This task owns only
Pennix source changes; the parent owns installation and integration evidence.

- Grok v0.3.0 was released first. Final review found missing PATH-first wording;
  the same approved documentation requirement was corrected in source and
  published as v0.3.1 without runtime changes. The final snapshot is source
  `85abc396bd8b6900ca5e3b4c22ad6c5ad395140e` from `v0.3.1`; archive SHA256:
  `3005b8b86cd2d016693aefbf374effa37e93002fa34677fa2733ba3cc6c99e65`.
- Windsurf v0.1.16 native release-evidence reconstruction passed. Its registry
  tarball SHA256 is `ae41d635079dd49a38b9ef5d7b4fe0bfc047d10eaf074b405c780dfa2b4dff8d`.
  All runtime files match the package. The consumer retains one existing
  documentation deletion of a retired product name, already owned by source
  commit `9409047e167873ab7de49cb45884cc5dd4907321`; the projection is therefore
  not described as byte-identical to the tarball. No runtime version is issued.
- The catalog drops the active Firecrawl target and declares only the finite
  Grok command export. Schema 2 binds the command map and tree digest. Explicit
  replacement upgrades safe schema 1 receipts, rejects drift and unowned paths,
  protects PATH ownership and restores the tree/receipt/new links on failure.
- The retirement reconcile validates the old profile digest and record shapes,
  preserves unrelated selections and credentials, verifies writes, and removes
  only the exact old cooldown. The actual parent-host reconcile removed only
  the retired catalog selection from the profile; no Grok secret was changed.
- Windsurf configure and readiness use a receipted collection entry, independent
  of any same-name PATH command. Native tool availability is defined in the two
  existing routing Skills; no server or Codex configuration change was made.

Validation before source submission: lifecycle/configuration/install suite,
both routing suites, syntax compilation and `git diff --check`. The parent
records final counts, source commit, installer staging and scoped live results.
No paid benchmark, other-device installation or unrelated service repair is
part of this task.
