# Footprint baseline alignment

Root coordination: `codex-workflow-optimization/.trellis/tasks/10-09-workflow-footprint-reconciliation`.

- Catalog changes are limited to FastCtx `0.2.23` and Ponytail `5.1.0` / `v5.1.0`.
- Ponytail upstream tag resolves to `9cc65d03aa2da1db7121b912d03596409ee340b8`. Native Codex removed/re-added only that marketplace at the approved tag and installed the enabled `5.1.0` plugin.
- All 136 lifecycle tests passed. No new lifecycle adapter, credential flow, configuration target, dependency or template was introduced.
- FastCtx `0.2.22` remains unpublished because its release guard rejected the legitimate lowercase Trellis `agents.md`; the immutable `v0.2.22` tag is unchanged. CI run `37870858757` successfully released `0.2.23`: all five platform jobs, final distribution validation, npm publication, and GitHub Release `v0.2.23` passed. The public registry lists `0.2.23` for `@pennixrv/fastctx`.
- Published catalog commit `b5f471b2e4d6cd7070c7a2c06171476bf29e0129` was installed by system SkillInstaller in git mode, using all 11 catalog paths. Native validation confirmed exact Skill names and executable seed; native `replace-staged` completed with zero npm vulnerabilities.
- All 134 tracked collection files and their modes match the source; native receipt integrity is `match`, staging is absent. The installed catalog correctly pins FastCtx `0.2.23` and Ponytail `5.1.0` / `v5.1.0`.
- Native lifecycle upgraded only FastCtx; native Apply refreshed its consumption binary. CLI and Apply binary are both `0.2.23`; applied state, binary and nine-tool contract pass. Full lifecycle verification is `match`, 14 components checked, `failures=[]`; only Codex CLI upgrade availability remains an advisory. SiYuan stays enabled/configured; no private credential was copied.
- Relevant 136 lifecycle tests, catalog parsing and `git diff --check` pass. All task acceptance criteria are met; the native task archive and owner journal close the records.
