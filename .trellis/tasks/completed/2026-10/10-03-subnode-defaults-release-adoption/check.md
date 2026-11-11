# Catalog checkpoint

The only source behavior change is trellis-cli.approved_version from 0.7.0-beta.23 to 0.7.0-beta.24; its existing assertion is aligned. `python3 -B -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p 'test_lifecycle.py'` passed all 60 tests. No lifecycle mechanism, static template, credentials or unrelated component version changed.

Catalog publication/deployment waits for the native Trellis beta CI and public pair visibility. Consumer asset and installed collection results will be appended after those protocols complete.

## Native beta.24 candidate dispositions (2026-10-03)

Native create-new completed; candidates were compared with existing bytes. Preserve inline execution and project-specific roles. No hashes/provenance are hand-edited.

- `.trellis/config.yaml.new`: accept native candidate; preserve existing file mode.
- `AGENTS.md.new`: accept native candidate; preserve existing file mode.

Native workflow preview equals the current updated workflow byte-for-byte. Explicitly select native @ beta.24 to materialize provenance, verify it, then remove only the accepted workflow.md.new sidecar.

## Published adoption checkpoint

- Project version is 0.7.0-beta.24; all eight profile bytes and the native receipt equal published source SHA256 b862bd997cb8874ae0e167ca47abcd315840e6a6102373c3e516e969f14ee8a2. Python scripts and present Codex hooks parse successfully.
- Native post-update dry-run has no remaining new/auto-update files. CCH/Windsurf retain exactly the five declared custom files and previously deleted native agent assets; other updated projects are already up to date. No directory-wide force, migration, private configuration, or hand-edited metadata was used.
- Root and FastCtx provenance verify codex-subnode-channel @ 8f7a3741a107288ffe30a6c6ccc413f68d470c97; Trellis and Skills explicitly verify native @ beta.24.
- Scope is released defaults and consumer adoption. Prior two read-only/no-tools route smokes establish Sol/high and Luna/xhigh reachability only; role quality, full Channel/report reliability and the three downstream tasks remain outside this acceptance.
- Source catalog 5adc967 is pushed to origin/main. System SkillInstaller used git mode at that exact commit for all 11 paths; native replace-staged installed the whole collection with executable seed-arch.sh, then lifecycle upgraded Trellis. Scoped verification of trellis-cli, pennix-skills, codex-config and codex-agents all match. Installed config/AGENTS were already current. Pre-existing AoE drift remains outside this upgrade.

Post-promotion native update refreshed receipt baselines. Trellis/Skills have zero existing-byte receipt mismatches; CCH/Windsurf retain exactly the five already accepted customizations through native --skip-all. No new candidates or asset byte changes arose.
