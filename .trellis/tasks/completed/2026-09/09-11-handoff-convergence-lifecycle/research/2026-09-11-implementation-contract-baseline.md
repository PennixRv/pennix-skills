# Handoff lifecycle 实施合同基线

**状态：** 已进入实现；只修改 `pennix-skills` checkout，未安装宿主副本，未修改、写入或调用 OpenViking 远端。

- `handoff.py` 当前为 schema v4，已有 `_payload_digest`、`_verify_rollout`、`validate` 和
  `_atomic_json`；兼容扩展必须复用它们，不能重写 rollout parser。
- `render_handoff_prompt.py` 先执行 exact validate，只有 `ready` 才原子生成 paired prompt；这条
  ready-only gate 是不可退化的既有合同。
- `workflow_contracts.py` 已集中 canonical JSON digest、bounded text/list 与 secret detection；新增
  receipt/observation 必须在此扩展，避免多处不同 decoder。
- 本轮复现证明 formal target intake 的 `reconciled` 不能被视为 task 已绑定：新 session identity
  已存在但没有自身 pointer 时，旧 Trellis resolver 会借用 foreign source pointer。Trellis fork 先修复
  后，本 task 的 consumer 仍必须显式拒绝 `session-fallback:<foreign-key>` 作为 target binding 证据。
  后续用户授权才使用原生 `task.py start` + `current --json` 取得 `session:<target-key>`；完成 task
  走精确 native archive，Pennix 只记录 disposition，绝不写 task/session state。
- 当前 OpenViking 只读证据为 `management_observable`，未验证 archive boundary/session mapping/Task
  retention/timeout/purge；因此高等级 mode 只能 fail closed。
- Trellis session-isolation 修复已发布为 `v0.6.25`（源码提交 `24ee1ee717656ced304574562d08b3ea767161c3`，
  当前宿主 CLI/Core 均为 `0.6.25`）；该版本修复 known context key 缺少自身 pointer 时错误借用
  foreign pointer 的问题。它不改变本 task 的边界：handoff 仍须把 rollout `session_id` 当作 provenance，
  并在后续 activation 复核直接 `session:<target-key>`。
- 禁止读取 Plugin private state、shell HTTP fallback、远端写入/删除、Trellis/context-mode/OpenViking
  源码修改和 `/home/penn/.codex` runtime config 修改。

## 已落地的实现事实

- `workflow_contracts.py` 现在集中校验 lifecycle mode、observation、attestation、bounded digest 和
  safe id；未知字段、secret、路径穿越、非法 `session-fallback` target source 都 fail closed。
- `handoff.py` 保持 v4 `write/validate` 和 rollout parser 不变，新增三轴 append-only receipt：
  `prepare`、`finalize`、`admit`、`status` 与 `retention archive|restore|reopen|purge`。receipt 绑定
  `handoff_id + core.integrity.payload_digest`，每个 handoff 文件在一个 advisory lock 内重新读取链尾、
  校验 transition、计算幂等事件 ID 后 fsync 追加；相同操作重试返回 `idempotent`，链断或不合法状态拒绝。
- source rollout `session_id` 的 provenance 与 target direct `session:<target-key>` 已分离并有回归测试；
  target 必须由当前 `task.py current --json` 直接返回相同 source，且不能复用 handoff source session。
  `admit` 只记录 reconciliation，`action_authorized` 仍被 contract 固定为 false，不启动/关闭/改写 task。
- retention 只处理 core 和 paired prompt。archive 采用临时目录 copy、hash/schema 检验、fsync/rename；
  purge 需要 exact handoff id 和已验证 archive，只删除 canonical core/prompt，receipt、task、rollout、
  logs 和远端数据不受影响。restore 即使 canonical core 已被 purge，也只从同 ID archive 恢复并重新校验。
- renderer 在 core `ready` 之外再读取 lifecycle status；高等级 mode 没有对应 observation proof 时不生成
  paired prompt。`core_only` 无 receipt 时保持既有 ready-only 行为。
- 当前回归结果：`python3 -m py_compile skills/pennix-session-handoff/scripts/*.py` 通过；
  `python3 -m unittest discover -s skills/pennix-session-handoff/tests -v` 共 11 项通过；覆盖旧 v4、
  receipt 幂等/并发、pending lifecycle、source/target provenance、copy-first archive、purge/restore/reopen、
  secret/path/symlink 和 renderer gate。
