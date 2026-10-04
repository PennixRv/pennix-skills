# Pin verified Trellis beta30 and refresh installed Skills

## Goal

Keep the Pennix lifecycle catalog and installed Skills collection aligned with the verified Trellis beta30 metadata-cleanup release.

## Requirements

- Change only the Trellis CLI approved version from beta29 to beta30 after both npm artifacts are published and verified. Preserve every other component pin and the existing ten-skill collection.
- Commit/push the source catalog on `main`, install the exact source collection through `$skill-installer` staging + native transactional replace, and use lifecycle discover/upgrade/verify for only `trellis-cli`.
- Preserve user static configuration, credentials, tasks/ledgers, unrelated dirty state, and all other component installations. Do not add any memory/knowledge-base component.

## Acceptance Criteria

- [x] Catalog has exact `0.7.0-beta.30` Trellis pin and no other behavioral/catalog change; lifecycle tests and collection check pass.
- [x] Source commit is pushed, exact ten-skill collection is installed transactionally and integrity verify returns match.
- [x] Native lifecycle upgrade installs the published beta30 CLI/core pair; component verify passes and the installed migration metadata contains no retired product names.

## Planning Seal / implementation

User approval covers full removal plus publication/install/consumer refresh. This is a bounded existing catalog-pin update. Source owner is this repo on `main`; only the approved Trellis pin changes. Wait for CI and npm visibility before editing the pin; run existing lifecycle tests/source check, exact staging replace and native single-component upgrade. On test, source/install integrity, or package publication mismatch, stop without touching any other component. No new decisions or abstractions are required.

## Verified completion

Trellis publication run `37187903780` succeeded; CLI/core and beta dist-tags are `0.7.0-beta.30`. Catalog and matching test-fixture commit `ce3676ef50eb67bafd55be259fb67d412e2a9e32` is pushed; lifecycle 127 tests pass. Native SkillInstaller staged that exact ten-entry source with preserved executable modes; transactional replace succeeded and collection verification is `match`, with no missing skills or staging candidates. Native lifecycle upgraded only `trellis-cli`; fresh component verification is `match`. Installed source and packaged migration metadata have no retired product names. Project-native beta30 version/provenance receipts are included with this owner task. Nine exact ignored orphan bytecode files from retired modules were dry-run verified and removed separately; no broad cache deletion occurred. Other component pins/configuration and private user state remain untouched.
