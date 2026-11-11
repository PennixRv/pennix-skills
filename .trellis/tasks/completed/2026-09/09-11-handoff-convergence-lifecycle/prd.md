# Implement Pennix handoff convergence lifecycle

## Goal

在不修改 OpenViking 源码、官方 Plugin、NAS 服务、Trellis runtime 或 `context-mode` 的前提下，扩展
`pennix-session-handoff`：保留 immutable core v4 兼容性，同时提供 source convergence observation、
target admission、接纳后的 retention/restore/reopen/purge，以及与 core digest 绑定的 append-only
lifecycle receipt。OpenViking 只是经验证的官方观察面，不参与 core `ready`、Trellis task 关闭或
pending action 授权。

## Requirements

### R1. Immutable core compatibility

- 现有 schema v4 `session-handoff.json`、payload/source digest、rollout path/device/inode/prefix 校验和
  `write -> validate -> render` 行为不变；新操作绝不改写 core。
- lifecycle sidecar 绑定 `handoff_id + core.integrity.payload_digest`，独立存储、独立 digest/CAS、
  仅 append。core ready、target admission、retention、OpenViking convergence 是不同事实。
- 新输入使用集中 decoder、固定大小上限、secret/path 校验与稳定 reason code；不保存凭据、Plugin
  private state、完整 transcript、raw tool I/O 或未脱敏外部响应。

### R2. Three-axis lifecycle

- source：`prepare` 固定 mode 与最后有效 boundary intent；`finalize` 在 source 正常结束后只读取经
  验证的官方 observation manifest。不会执行 commit、写 Plugin state 或无限等待。
- `source.rollout.session_id` 仅表示 rollout 采集来源的 provenance；它既不是当前 Trellis
  `context_key`，也不是 target pointer，更不能被复制为目标会话的绑定证明。source/target identity
  必须在数据模型和 reason code 中分开表示。
- target：接收会话再次 `validate=ready`、完整读 prompt、运行 `$trellis-start` 并核对当前
  task/Git/evidence/CR 后，以有限显式 attestation 记录 disposition；绝不执行 pending next action。
  初始 intake 停止不等于 target 已绑定。获得后续明确继续授权后，必须确认当前 session identity
  是直接解析结果，并由 Trellis 原生 `task.py start` 建立/验证 target pointer；若 resolver 返回
  `session-fallback:<source-key>`、identity 缺失或 key 不匹配，target 必须保持未绑定并停止。
- target closure：若接收时 task 已有充分完成证据，不为制造 pointer 而执行 `start`；应在确认
  exact task path 后走正常 Trellis finish/archive，并验证 archive 清除了该 task 的旧 pointer。
  这一步是 task 生命周期动作，不由 Pennix Skills 自己实现第二套 task 状态机。
- retention：admission 后进入 `archive_eligible`，copy-first 验证后可 `archived/retained`；支持精确
  restore/reopen/expiry/purge。不得向 immutable core 写 `consumed`/`closed`。

### R3. OpenViking guarantee levels

- 默认 `core_only`，不需要远端写入。`capsule_required` 必须有单独用户授权和官方 write/create + exact
  read digest；不是本任务默认部署行为。
- `archive_required` 需要 source boundary、稳定 source-session mapping、官方 archive exact read；
  `convergence_required` 还需要 Task `completed`、completion artifact 和 memory-diff exact read。
  前置缺失必须返回 `unsupported|unavailable|pending|failed`，不得静默降级。
- 脚本不读 Plugin private state、不复制 transcript parser、不用 shell HTTP 绕开工具路由。finalizer
  仅消费一个有界可信 observation manifest；当前管理面只达到 `management_observable`。

### R4. Retention safety

- sidecar 置于 `.trellis/.runtime/handoff-lifecycle/<handoff-id>.jsonl`，归档副本置于
  `.trellis/.runtime/handoff-archive/<handoff-id>/`，均不入 Git。
- `archive` 仅复制明确 core 和（若存在）paired prompt：先 hash/size/regular-file 验证、临时目录
  copy、fsync/rename、再 append receipt；不扫描或复制 rollout/task/session/memory/resource/watch。
- `restore/reopen` 只从同 id archive 恢复且目标缺失或 digest 相同；`purge` 要 exact handoff id、
  已验证 archive 和明确确认，只删除 core/prompt，不联动删除任何 task、rollout、日志或远端数据。

### R5. Skill and routing ownership

- 扩展现有 `pennix-session-handoff`；不新增第二个 lifecycle Skill、Hook、daemon、scheduler 或状态机。
- 更新 `pennix-workflow-routing`：CR 是 Trellis readonly input，core/receipt 是 Pennix 所有，OpenViking
  是候选观察，`/home/penn/.codex` 是安装/静态资产面。
- `pennix-skills` 不管理 Trellis session pointer/task、Plugin cache/config/trust state 或 Git 中的服务数据。

## Acceptance Criteria

- [ ] 现有 handoff tests 全通过；旧 v4 core 的 validate/render 结果、退出码和 ready-only gate 兼容。
- [ ] receipt chain/digest/CAS、合法状态 reducer、重复操作幂等、半写/链断、core/prompt drift、
  secret/path/symlink/size 拒绝和并发有测试。
- [ ] prepare/finalize/admit/retention 精确区分 core-only、pending、unsupported、unavailable、failed、
  archive_verified、converged；无外部证据时不能产生高等级保证。
- [ ] target admission 不执行 pending action、不关闭 task、不改 core；copy-first archive、restore/reopen
  和 precise purge 使用临时 project tests 证明不越界。
- [ ] target admission/后续 activation 明确区分“已读并核对”与“已绑定”：不会接受 foreign
  `session-fallback` 作为 target；未完成 task 只通过原生 `task.py start` 绑定并复核
  `source=session:<target-key>`；已完成 task 可直接精确 archive，且不伪造 start。
- [ ] source rollout 的 `session_id` 在 admission/binding 测试中只能作为来源 provenance；不能
  充当 target identity、不能生成 target pointer，且 target 只能接受当前会话直接解析出的
  `session:<target-key>`。
- [ ] Skill/renderer/routing 明确官方 MCP/CLI 观察与失败停止；不新增 Hook、remote client 或 Plugin
  state 读取。
- [ ] 通过适用 Python/lint/security/`trellis-check`、Git diff 和 GitNexus（若存在）验证，提交并推送
  后将 commit 和限制交给根仓库集成；不在本 task 直接重装宿主或变更 context-mode。

## Out Of Scope

- OpenViking/NAS/Plugin/MCP 配置、远端 session/task/archive/memory/resource/watch 的写入、删除或源码修改。
- Trellis CR 实现、context-mode/RecoveryBrief 退役、FastCtx 切换、host runtime 配置/Hook trust state。
- 在 core、Trellis task JSON 或 Git 写 lifecycle runtime receipt。

## Notes

- 这是复杂 task；激活前必须有 `design.md` 与 `implement.md`。当前仍为 `planning`，不得把工件补齐
  误报为源码实现或部署。
