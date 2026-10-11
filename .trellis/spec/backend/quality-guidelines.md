# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

<!--
Document your project's quality standards here.

Questions to answer:
- What patterns are forbidden?
- What linting rules do you enforce?
- What are your testing requirements?
- What code review standards apply?
-->

(To be filled by the team)

---

## Forbidden Patterns

<!-- Patterns that should never be used and why -->

(To be filled by the team)

---

## Lifecycle Verification Contract

- `verify --component <key>` validates only the selected catalog component and
  fails closed for an unknown key. It must not evaluate unrelated components,
  static assets, or configuration targets.
- Full `verify` checks every catalog component and the core/enabled
  configuration targets. Its result distinguishes `scope`, `failures`, and
  `advisories`; only failures make the status `blocked`.
- A readable installed version below a readable `repository-latest` candidate
  is `upgrade-available` and is advisory. Missing, unknown, unsafe-owner,
  pinned-drift, static/collection integrity failure, upstream failure, and
  required configuration readiness failure remain blocking.
- For AUR packages, compare the CLI-reported version with the repository
  version without the trailing Arch `pkgrel` (for example, `0.156.1-1` versus
  `0.156.1`), while retaining the complete candidate version in inventory.
- Tests must cover scoped isolation, unknown selectors, repository candidate
  advisories, candidate-unavailable blocking, pinned drift, and full
  configuration checks.

---

## 会话交接接纳合同

- Schema 11 通过 core 的 `history` 元数据绑定同目录的
  `session-handoff-history.jsonl`，记录固定文件名、SHA-256、字节数、Unicode
  字符数、类型记录计数和捕获边界。随历史增长的候选、时间线、覆盖区间和工具
  关联只存于 JSONL；时间线引用候选序号。
- 渲染、读取、生命周期变更、所有权操作或保留操作前，校验所有将被使用的字段和
  交叉引用。整数校验拒绝布尔值；包格式错误通过受控合同错误返回。
- core 与 history 视图为只读、确定性序列化的 UTF-8 文本，偏移量按 Unicode
  字符计算。读取范围不修改交接包，也不创建持久游标。接纳收据记录实际读取的
  历史范围；结构校验不代表代理已语义阅读。
- 当前入口拒绝旧 schema。普通文件工具可以检查旧资产，但不得迁移旧包或沿用旧
  生命周期、接纳语义。
- 测试覆盖共享入口拒绝畸形字段、长 Unicode 文本无损分页、收据范围边界和历史
  写入授权门。
- 写入、校验和收据扫描不保留随历史规模增长的数组。SQLite 索引仅存于本次操作的
  私有临时目录，缓存有界且临时数据写入文件。内存占用随最大单条记录、core、
  请求页和固定缓冲区增长；耗时和临时磁盘用量可以随规模增长。使用 192 MiB
  进程内存限制测试 1k/10k/100k 记录及 8 MiB Unicode 单条记录；资源门失败时不得
  缩小规模。
- 检查解码后的字段值是否命中已知秘密模式；只脱敏历史中的敏感片段或值，请求、
  core 和收据命中则拒绝，并且不得回显可疑内容。测试包括带引号、转义和嵌套的
  JSON、token/xai/Bearer/私钥、普通文字及受控 CLI 错误。检测范围仍是有限的。
- 归档和恢复先校验 core/history/prompt，再以原子方式整体发布；清除通过目录切换
  移除整包，收据写入失败时恢复原目录。目标目录含未知资产或归档字节不一致时
  停止。Trellis 原生任务所有权仍只绑定 core_digest；core 负责绑定其历史文件。

---

## Required Patterns

### Skill collection deployment boundary

- The repository checkout is the source of truth. The installed collection is
  a replaceable delivery copy and must not become an edit location.
- `pennix-skills-install` defaults to
  `${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills`, but callers may pass an
  explicit `--dest` ending in `skills/pennix-skills` for a host-selected
  discovery root. `PENNIX_SKILLS_ROOT` is a caller convention for reusing that
  selected collection root in direct Skill commands; the installer does not
  scan for roots or persist host-wide discovery state.
- Changes to this boundary require tests for the unchanged default, an
  explicit host-selected root, invalid destinations, and atomic replacement.

### Collection commands and configuration owners

- Schema 2 receipts bind the tree digest and the finite catalog command map.
  Explicit `replace-staged` may migrate a verified schema 1 tree; it may not
  overwrite an invalid or drifted receipt. Collection, receipt and newly
  created command links roll back together on replacement failure.
- A user command link must be absent or match the existing receipt and exact
  collection target. Unowned paths and other `CODEX_HOME` targets are conflicts;
  PATH shadowing is reported independently of the link's state.
- Windsurf readiness and configuration resolve its native executable from the
  receipted collection. They never select an arbitrary same-name PATH command.
- SiYuan owned helper commands may use a different absolute interpreter path
  only when filesystem samefile proves the expected executable and the two-item
  argv keeps the exact installed helper path. Other fields and owned stanza
  bytes remain strict; readiness never rewrites configuration or credentials.
  Unverifiable paths, changed scripts or interpreters, and extra argv fail closed.
- Retired configuration migration uses explicit `reconcile`, validates private
  files and known record shapes before writing, preserves other credentials
  and target selections, verifies writes and reports partial failures closed.

### Profile digest reconciliation

1. **Scope / trigger:** A configuration catalog change may leave a valid current
   namespace profile stale. Only explicit workflow-state reconciliation refreshes
   it; component installation and readiness probes do not configure credentials.
2. **Signature:** `python3 skills/pennix-component-lifecycle/scripts/lifecycle.py
   reconcile --component pennix-workflow-state --yes` retains the existing CLI.
3. **Contract:** The private profile has exactly `schema: 1` (integer, not bool),
   a lowercase 64-hex `catalog_digest`, and a unique string `targets` array.
   Namespace directories are owned and mode 0700; the profile is owned, regular,
   mode 0600, and has no symlink ancestor. Every selected ID belongs to the current
   catalog. Only default-enabled and selected targets are probed, using the same
   local adapter calls as discovery. All must be `ready` or `configured`.
   A refresh changes only the digest value, preserving target order and selection.
4. **Validation / errors:** Safe stale profiles return `refreshed`; current ones
   return `already-match` without rewriting. Invalid shapes, unknown targets,
   unsafe paths/modes, and readiness failures return `blocked` without a write.
   Compare the original bytes before atomic replacement, verify written bytes,
   and roll back only while the destination still equals this attempt's output.
   Preserve concurrent external bytes and report `blocked` with
   `rollback-incomplete` when restoration cannot safely complete.
5. **Cases:** Good: a renamed catalog member with unchanged target IDs and ready
   adapters. Base: a current profile needs no write. Bad: a removed target ID or
   an unready core provider cannot be approved merely by replacing its digest.
6. **Tests:** `test_lifecycle.py` asserts ordered targets, default/selected probe
   coverage, no configure/prompt, idempotence, invalid/private-path rejection,
   pre-replacement comparison, write/readback failures and external-byte survival.
7. **Wrong / correct:** Do not re-run configure to refresh a digest or overwrite
   third-party bytes during rollback. Use explicit validated reconcile and keep
   full host verify separate from profile reconciliation.

---

## Testing Requirements

<!-- What level of testing is expected -->

(To be filled by the team)

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
