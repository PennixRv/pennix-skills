# beta.26 source and consumer check

2026-10-03. Catalog source, staged installation and native consumer update passed.

- Catalog pins `@pennixrv/trellis` `0.7.0-beta.26`; existing lifecycle contract assertion updated. `python -m unittest discover -s skills/pennix-workflow-lifecycle/tests -v`: 132 passed. Source commit `b55151cd57c700d72756682eade2750ce7161292` is pushed to owner `main`.
- The system SkillInstaller staged the catalog-defined collection from that immutable commit. Exact names/frontmatter and executable `seed-arch.sh` passed before native `replace-staged`; lifecycle reports the collection receipt matches.
- Scoped lifecycle verification passed for `pennix-skills`, `codex-config`, `codex-agents`, and (after install) `trellis-cli`.
- This project reports `.trellis/.version=0.7.0-beta.26`, native workflow provenance verifies at beta.26, and the bundled worker guidance contains `--workers`. Native `trellis update --skip-all` updated the three Channel references and receipt; follow-up dry-run has no pending update.
- Main/base are self-referential for this bounded direct-main adoption. The task was not PR-backed and will use the native `archive --skip-branch-validation` exception.

Task archive/journal/push and exact consumer commit are recorded after the scoped commit.
