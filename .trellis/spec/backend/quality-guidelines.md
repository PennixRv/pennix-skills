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

## Collection Manifest Contract

- `collection.json` is the only maintained member, license, command and
  materialized-source declaration. `scripts/collection.py verify` checks it
  without importing Lifecycle code or fetching a mutable catalog.
- Source members live at `skills/<name>`; installed commands use
  `<name>/<relative-command-path>`. Require exact membership, valid unique
  JSON/YAML keys, matching Skill identity, nonempty declared licenses and
  executable commands. Reject symbolic links in member trees.
- Materialized sources use a full Git commit for both `ref` and `commit`, a
  declared `archive` or `npm-pack` snapshot mode, and only supported
  `post_install` identifiers. Malformed types and unsupported source fields
  fail with a controlled contract error before synchronization.
- Synchronization first runs `collection.py sources`, materializes those fixed
  sources, then revalidates the collection and runs root, Skill and evaluation
  tests. `sources` validates the manifest before member trees exist; full tree
  checks belong to `verify`. Fix and publish the real source before regenerating
  its snapshot. Compare the complete generated file set and bytes against the
  fixed archive or package; a correct manifest alone does not prove that a
  checked-in snapshot matches its source or preserves the intended rules.
- Lifecycle independently validates the delivered manifest as untrusted data.
  Its catalog pins the collection repository and manifest location; its native
  lock and receipt bind the installed revision. Do not copy a member table,
  execute a staged collection's verifier during installation, or add a
  collection-CI dependency on Lifecycle's mutable catalog.

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
- Lifecycle owns installation, replacement, command links and receipts through
  its native `pennix` entry. This repository owns source content and validation.
- Skill identity is logical. Use the host-declared physical path, expand only
  its declared root alias, preserve collection levels, and resolve references
  from the actual loaded `SKILL.md` directory. Do not guess a flattened path.
- Static path checks cover main, extra, project and relative paths. Native
  evaluation receipts retain failed attempts; only attributable successful
  reads count as `read`, without claiming full agent consumption.

### Collection commands and configuration owners

- The manifest owns the command map. Lifecycle owns deployment and verifies
  the exact receipted executable before invoking a connection owner; an
  arbitrary same-name PATH command is not an equivalent source.
- SiYuan's Skill owns its private connection record and header helper.
  Lifecycle owns Codex MCP registration and preserves unowned configuration.
  Do not introduce a second Codex TOML writer in the Skill.
- Explicit takeover of an existing private connection requires an exact
  same-content match and valid ownership evidence. Different content or
  external drift blocks writes. Failed writes restore only this attempt's
  output, preserving concurrent external bytes and reporting incomplete
  rollback. Tests use isolated private paths and synthetic credentials.
- Global user-rule templates, installation receipts and configuration
  migrations are contracts of the independent `pennix-lifecycle` repository.
  Keep only entry navigation here; do not revive the removed embedded executor
  or its profile reconciliation protocol.

### Routing Skill verification

- Static checks verify stable parameter identifiers and resolvable Skill links;
  do not freeze Chinese sentences or require delegated rules in multiple files.
  These checks establish document integrity, not model routing behavior.
- Compare fixed before/after inputs against actual tool calls, including the
  first Skill read and ordinary reads after a component-native command. A
  `native_cli` label does not exempt `cat` inside the same shell command.
- For example, read a mandatory PRD fully through the host's bounded file entry;
  ordinary `task.py current` may use Context Mode if cwd, native identity, exit
  code and complete receipt are preserved. Do not route host continuations there.
- Record source, installed revision and behavioral results separately. Keep raw
  traces outside Git, enforce the agreed model-call budget, and report failed,
  blocked or untriggered coverage without converting it to a pass. Installation
  success alone cannot establish that a routing recurrence is fixed.

---

## Testing Requirements

<!-- What level of testing is expected -->

(To be filled by the team)

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
