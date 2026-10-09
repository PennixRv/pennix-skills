# Footprint baseline alignment

Root coordination: `codex-workflow-optimization/.trellis/tasks/10-09-workflow-footprint-reconciliation`.

- Catalog changes are limited to FastCtx `0.2.22` and Ponytail `5.1.0` / `v5.1.0`.
- Ponytail upstream tag resolves to `9cc65d03aa2da1db7121b912d03596409ee340b8`. Native Codex removed/re-added only that marketplace at the approved tag and installed the enabled `5.1.0` plugin.
- All 136 lifecycle tests passed. No new lifecycle adapter, credential flow, configuration target, dependency or template was introduced.
- Installed collection replacement and complete lifecycle verification remain pending; publication of this catalog change alone does not close the task.
