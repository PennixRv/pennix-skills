# 集成 Hindsight 到 Pennix 生命周期部署与校验

## Goal

为根协调任务 09-27-hindsight-memory-base-migration 实现 Hindsight v0.10.1 与 coding-agents 0.6.1 的可重入 Pennix 生命周期集成：静态部署资产与密钥注入分离，版本锁定，Codex hooks/MCP/官方 Skill 幂等合并与移除，Trellis 项目登记/稳定 bank 路由，OV 活动 catalog 与插件安装退役。目标分支 main。

## Requirements

- Pin and install only `@vectorize-io/hindsight-coding-agents@0.6.1`; Hindsight service version and API URL are owner-provided inputs. Use the upstream `install codex` / `uninstall codex` workflow for Codex registration, not a fabricated Codex plugin or copied installer behavior.
- Provide idempotent Pennix `discover`, `install`, `upgrade`, `configure`, `verify`, and `uninstall` behavior for the selected Hindsight integration. Repeated install/upgrade/configure/uninstall must preserve unrelated Codex hooks, MCP servers, Skills, and Hindsight config.
- Separate non-secret settings delivery from secret entry: static Hindsight settings omit `apiToken`; the explicit secret configuration target obtains the API bearer token through hidden interactive input and merges only that field into upstream `~/.hindsight/coding-agent.json` with owner-only permissions. This file is Hindsight's native config boundary; no new vault, shell wrapper, env distribution framework, or secret in source/arguments/logs.
- Hindsight client settings: self-hosted API URL supplied by the NAS owner, `optInOnly=true`, `autoReflect=true`, `autoUpdate=false`, `autoSeed=false`, `codebaseSurvey=false`, `gitIngest=none`; use upstream Stop write-back and preserve unrelated native values. `autoReflect` is the pinned package's one-time first-prompt recall setting; bound it by the upstream Codex hook's low-budget/20-second behavior and preserve its Hindsight-memory attribution. `autoInject` is not a supported setting. Any other value not directly supported by v0.10.1/coding-agents 0.6.1 is a stop condition, not a silent fallback.
- Provide explicit Trellis-project registration. Persist a stable `pennix.memory.bank_id` under project-controlled `.trellis/config.yaml`; map the canonical project root to that bank through Hindsight `mapPathToBank`; do not enable all directories or derive identity from basename. Deregistration removes only the selected mapping and leaves project identity/history intact.
- Replace the OpenViking lifecycle catalog/config target and native uninstall path only after Hindsight installation/readiness is proven. Hindsight verify is redacted and checks package version, Codex Hook/MCP registration, static policy, token readiness, and explicitly registered project mappings.
- Keep application state out of `~/.codex/pennix-workflow-lifecycle`; use the current Pennix lifecycle state owner/path, and leave unrelated legacy paths untouched unless the separate retirement inventory proves they are OpenViking-owned.

## Acceptance Criteria

- [ ] An isolated temporary `HOME` integration test (with `CODEX_HOME` unset or equal to `$HOME/.codex`) installs/upgrades/verifies/uninstalls pinned 0.6.1 and proves a second run is idempotent while unrelated Codex config remains semantically intact. A custom `CODEX_HOME` that differs from `$HOME/.codex` is rejected before edits because the pinned upstream installer ignores it.
- [ ] Static defaults are materialized without `apiToken`; secret configuration separately prompts without echo, stores only in the native Hindsight private config with mode `0600`, and all command output/verify is redacted. Reapplying static settings preserves the token; removing Hindsight removes only Hindsight-owned entries and credential field.
- [ ] Codex uses the official Hindsight coding-agent hooks and MCP server with only `codex` harness; the one-time first-prompt `autoReflect` is enabled, while auto-updater, survey, Git seed/ingest, and global all-project capture are disabled.
- [ ] With `optInOnly=true`, unregistered project paths do not retain, recall, or expose project memory. An explicitly registered project gets a stable valid ID from `.trellis/config.yaml`, maps the current canonical path, shares identity across worktrees per the selected Hindsight behavior, and can be remapped after relocation/new-machine setup.
- [ ] Invalid/ambiguous Trellis config, duplicate/empty bank IDs, path alias/symlink ambiguity, unrelated user-owned Hindsight config, missing API token, wrong package/version, custom `CODEX_HOME`, or conflicting Codex registration fails closed without partial destructive edits.
- [ ] No static/template/secret artifacts, lifecycle state, or plugin staging residue is written under an unintended `~/.codex/pennix-workflow-lifecycle` path; no credential enters repository/task/log/cache.
- [ ] Active OpenViking catalog/connection setup is removed only after exact native uninstall is verified; no generic OpenViking source or user data is deleted by this task.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
