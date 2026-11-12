# Quality Guidelines

Collection, document Skill, handoff and evaluation contracts for this repository.
The existing path is retained for active references; it does not require a backend layer.

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

- 当前 rollout 定位通过 `handoff.py resolve-rollout` 的真实 CLI 回归验证：用宿主
  `CODEX_THREAD_ID` 精确查询只读 Codex 元数据，核验唯一记录、绝对普通文件及首条
  `session_meta.payload.id`。不得由当前日期、修改时间、旧交接包路径或扫描目录推导。
  归档后元数据路径可变化；结构不支持或身份冲突必须受控失败。测试使用合成 SQLite
  和 rollout，覆盖跨日、归档和拒绝场景，核对源数据不变；不提交真实数据库或转录。
- Schema 12 通过 core 的 `history` 元数据绑定同目录的
  `session-handoff-history.jsonl`，记录固定文件名、SHA-256、字节数、Unicode
  字符数、类型记录计数和捕获边界。随历史增长的候选、时间线、覆盖区间和工具
  关联只存于 JSONL；时间线引用候选序号。
- 渲染、读取、生命周期变更、所有权操作或保留操作前，校验所有将被使用的字段和
  交叉引用。整数校验拒绝布尔值；包格式错误通过受控合同错误返回。
- core 与 history 视图为只读、确定性序列化的 UTF-8 文本，偏移量按 Unicode
  字符计算。读取范围不修改交接包，也不创建持久游标。接纳收据记录实际读取的
  历史范围；结构校验不代表代理已语义阅读。
- 当前接纳和所有权写入仍严格要求 Schema 12。历史存储入口只读识别 Schema
  4/6/8/9/11，保留原始字节，不升级 schema、不恢复任务权限，也不宣称满足当前接纳。
- 测试覆盖共享入口拒绝畸形字段、长 Unicode 文本无损分页、收据范围边界和历史
  写入授权门。
- 再次交接的回归须经过真实 CLI 解析器，将当前代数传入
  `ownership quiesce --expected-generation`，同时验证首次交接省略该参数时仍从 0 开始。直接调用
  `ownership_operation` 不能代替该入口测试。
- 写入、校验和收据扫描不保留随历史规模增长的数组。SQLite 索引仅存于本次操作的
  私有临时目录，缓存有界且临时数据写入文件。内存占用随最大单条记录、core、
  请求页和固定缓冲区增长；耗时和临时磁盘用量可以随规模增长。使用 192 MiB
  进程内存限制测试 1k/10k/100k 记录及 8 MiB Unicode 单条记录；资源门失败时不得
  缩小规模。
- 检查解码后的字段值是否命中已知秘密模式；只脱敏历史中的敏感片段或值，请求、
  core 和收据命中则拒绝，并且不得回显可疑内容。测试包括带引号、转义和嵌套的
  JSON、token/xai/Bearer/私钥、普通文字及受控 CLI 错误。检测范围仍是有限的。
- 保留操作默认预览，写入必须绑定精确 ID 和新鲜预览摘要。当前包校验
  core/history/prompt；旧包按原始内容与身份投影限定资格。ZIP 是保留提交点，
  原始文件、旧收据和关联旧所有权记录均逐项记录 SHA-256；manifest 操作须与
  保留日志一致。归档保留展开源，清除先提交 intent，再切换目录并逐项退出；
  失败保留可恢复 ZIP 和精确残留，不宣称成功。恢复不授予当前任务权限。
- 固定 handoff 锁只保护短存储提交，不跨 Trellis Task CLI。跨 owner 操作先提交
  本地 intent；不确定结果保留并由原生代数、会话与包身份核对恢复，不重复 CAS。
  目标目录含未知资产、符号链接或归档字节不一致时停止。Trellis 原生任务
  所有权仍只绑定 core_digest；core 负责绑定其历史文件。

---

## Required Patterns

### Vendored document Skills

- `docx`, `pdf`, `pptx`, and `xlsx` are locally derived subdirectory imports,
  not whole-repository `materialized` members. Each `UPSTREAM.md` fixes the
  full source commit; `upstream-files.sha256` enumerates every original file.
  Compare the complete file set and unchanged bytes; local adaptations are
  explicitly enumerated. Do not weaken the materialized manifest schema.
- Run `python3 -m unittest discover -s tests -p test_document_skills.py -v`
  for provenance, exact license bytes, temporary profile cleanup and failure
  propagation. The LibreOffice wrapper may create an isolated profile but
  must not compile a shim or inject LD_PRELOAD to evade restrictions.
- Reading never saves or recalculates the source. In XLSX, load formulas and
  cached values separately; a missing cache stays unknown. A creation-only
  output constraint must not suppress a read-and-summarize request.
- Lifecycle owns document dependencies. Resolve the Python tool through uv's
  native directory and verified receipt; do not assume system imports or
  perform runtime pip/npm installation. Actual installed reading, rendering,
  OCR and discovery are separate integration evidence, not static test claims.

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
- Context Mode v2 follows its upstream adapter and the current host: bounded
  native output is valid; executors help derive results from large output.
  Do not reintroduce a mandatory executor wrapper or the removed integration
  Skill. Preserve per-call native fallback, complete-reading obligations and
  permission denials. Project cleanup affects the Git-common-directory database,
  including other worktrees; consult the actual native purge schema.
- Evaluation `--phase` only labels results. Require an explicit candidate
  CODEX_HOME, full collection commit, owner receipt and matching installed-tree
  digest. Reuse the registered provider auth command at runtime; never copy
  private authentication files into a fixture or summary.
- Record source, installed revision and behavioral results separately. Keep raw
  traces outside Git, enforce the agreed model-call budget, and report failed,
  blocked or untriggered coverage without converting it to a pass. Installation
  success alone cannot establish that a routing recurrence is fixed.

### 场景：固定来源的 Context Mode v2 行为评估

1. 适用范围：修改路由、路径加载或 Context Mode 消费指引时，核验真实候选的工具轨迹；静态检查不替代行为证据。
2. 接口：`python3 evaluations/run_codex_cases.py --phase before|after --output-dir <目录> --codex-home <绝对路径> --collection-commit <完整SHA> --provider-home <已配置HOME> --case <ID>`；`--retry` 追加保留失败后的新轮次。
3. 合同：phase 仅为标签；完整提交、owner receipt、集合树摘要须一致。候选会话须保留原生 rollout。Provider 只通过既有 auth.command 读取认证，不复制凭据。MCP 子进程的 CODEX_HOME 由 Lifecycle 显式配置，runner 不补造环境过滤结果。
4. 错误矩阵：receipt/ref/树摘要不匹配或符号链接拒绝运行；权限拒绝停止；本次能力故障保留实际回执再判断原生回退；输出大小限制按上游支持的有界分页处理，与访问权限拒绝分别判断。
5. 正常、基线及异常：小文件可以原生读取；强制全文材料须取得全部连续页；大型入口将条件细节渐进披露。错误路径不通过猜测目录弥补，未触发的失败分支记录未实测。
6. 验证：runner 单测覆盖来源缺失、摘要漂移及坏路径；collection verify 和链接检查验证实际成员。真实轨迹核对 Skill 声明路径、首读结果、MCP 线程身份、普通原生调用、全文页覆盖及失败停止点。
7. 错误与正确：只把 `--phase after` 改成新标签却沿用旧安装，不能证明新版行为；由 owner 物化固定候选并在每例前核验 receipt 与成员树，才形成可比较证据。真实模型和原生宿主压缩恢复是两种证据，分别记录。

### 原生提问评估

- `run_codex_cases.py --host app-server` 复用上述固定来源和预算，真实收发
  `item/tool/requestUserInput`；`--resume-thread <ID> --compact` 验证同线程原生恢复。
  协议 fixture 验证等待、答复、空答案和取消，真实模型另验实际选择，二者不能互代。
- Codex 0.167.0 的 Default 模式中，`request_user_input` 也产生
  `isBlocking=false`；Plan 模式才为 true。该字段不证明调用了异步工具。
  `question_tools(path, codex_home, thread_id, turn_id)` 仅审计宿主实际返回的
  sessions 文件，核验 session_meta 身份后按 turn_context 统计真实 function_call
  名称；路径越界、身份不符或超出预算均拒绝，不能从 UI 标志猜测名称。
- 回归必须覆盖 false 标志下同步调用、旧 turn 的异步调用不混入新 turn、身份及路径拒绝。
  summary 保留宿主标志与工具计数两类事实；未读取原生工具证据时保持 unknown，
  基线未复现不能改报为修复前失败。评估中未选异步，不代表宿主已技术移除该工具。
