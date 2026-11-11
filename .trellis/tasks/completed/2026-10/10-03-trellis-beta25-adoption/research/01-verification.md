# Verification record

Date: 2026-10-03

- Updated only `trellis-cli.approved_version` in the canonical lifecycle
  catalog from `0.7.0-beta.24` to `0.7.0-beta.25`.
- Updated the existing lifecycle catalog contract assertion to the released
  version.
- `python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p
  'test*.py'`: 132 tests passed.
- The catalog commit must be pushed before the Codex system installer stages
  the collection; the immutable source commit will be recorded after commit.
- Source commit `1d9039ff2b6d3cde39eea331e34a26791871fdaf` was pushed and
  used for system-installer git staging. Eleven entries, frontmatter, executable
  seed, and beta.25 catalog passed; native `replace-staged` completed.
- Native workflow preview changes exactly three recovery breadcrumb bodies.
  Accept the same native beta.25 template, then remove the exact identical
  preview. Native update uses `--skip-all` to preserve every modified asset.
- Global trellis-cli upgrade completed at beta.25. All four scoped checks
  (trellis-cli, pennix-skills, codex-config, codex-agents) report match and no
  failures. This project's two recovery scripts match the released template,
  all 100 managed receipt entries match, native provenance verifies at beta.25,
  and the accepted identical workflow preview was removed.
