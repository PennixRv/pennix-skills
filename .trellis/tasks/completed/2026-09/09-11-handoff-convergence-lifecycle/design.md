# Handoff convergence lifecycle 技术设计

## Separation of authority

交接存在三个独立对象：immutable core、lifecycle receipt、OpenViking observation。core v4 继续是
本地控制快照；它的 `ready` 只说明 rollout/task/Git/evidence 仍可复算。receipt 记录 source、target、
retention 的本地生命周期；OpenViking observation 仅在经官方能力验收后证明 archive/extraction。
三者均不能替代 Trellis 当前 task/Git 事实或用户对 pending action 的后续授权。

## Session identity contract

`source.rollout.session_id` 是 rollout 记录的来源 provenance，保留它只用于核对采集边界；它不
等同于 Trellis 的 `context_key`，不能写入 target pointer，也不能把 source task 带入新会话。目标
会话 identity 只来自目标运行时对 Trellis 的直接解析：后续明确授权后调用原生 `task.py start`，
再读取 `task.py current --json`，并要求 `source=session:<target-key>`。任何
`session-fallback:<key>`、缺失 identity 或 source/target key 不匹配都只能得到 `blocked/unbound`。
admit 阶段可以记录有限的 target attestation，但不得把 source session id 复制成 attestation 的
target identity；core 仍保持 immutable。

## Sidecar schema and reducer

sidecar 的固定布局：

```text
.trellis/.runtime/handoff-lifecycle/<handoff-id>.jsonl
.trellis/.runtime/handoff-archive/<handoff-id>/
```

每条 event 包含 `schema_version`, `kind`, `handoff_id`, `core_digest`, `event_id`, `event_type`,
`source_status`, `target_status`, `retention_status`, `observed_at`, `actor`, bounded `evidence_refs`,
`prev_event_digest`, `event_digest`。后者覆盖 canonical event（排除自身）。单 handoff advisory lock 内先重读并验证当前链尾、再校验
transition 并 fsync 追加，等价于以已观察链尾为 compare-and-append；相同 event id/digest 重试幂等，相同 id 不同内容拒绝。

| Axis | States |
| --- | --- |
| source | `unprepared`, `prepared`, `boundary_sealed`, `pending`, `archive_verified`, `converged`, `unavailable`, `unsupported`, `failed`, `expired` |
| target | `not_admitted`, `admitted`, `reconciled`, `blocked`, `disposed` |
| retention | `none`, `archive_eligible`, `archived`, `retained`, `restored`, `reopened`, `purged` |

reducer 只接受定义过的单向迁移和幂等重复；失败或重试不能回滚另一轴，也不能从缺失文件名推断状态。

## Target handoff admission versus task binding

目标会话生命周期必须拆成两个事实：

1. `admitted`/`reconciled`：目标会话完成 core validate、配对 prompt 阅读、`$trellis-start` 和
   当前 task/Git/evidence/CR 核对；这一步只记录有限 attestation，仍停在 pending next action
   之前。
2. `bound`/`closed`：用户在后续 turn 明确授权实际继续，且 Trellis 的当前 session identity
   被直接解析。未完成 task 才调用原生 `task.py start`，随后复读 `task.py current --json`，
   必须看到目标 task 且 `source=session:<target-key>`。若当前 resolver 只给出
   `session-fallback:<foreign-key>`，这不是绑定，必须返回 blocked/unbound。

   如果 task 在 target intake 时已经完成，则不调用 `start`；由精确 task path 走 Trellis 原生
   finish/archive，并在之后读取 task/archive 状态确认旧 pointer 已被清除。Pennix sidecar 只记录
   这次 disposition，不拥有或重写 Trellis task/session 状态。

这条区分修复了本次实际故障：已知新 session key 没有 pointer 时，Trellis resolver 错误借用唯一
旧 session pointer；handoff consumer 不能把该降级来源误当作新会话绑定。

## Commands and guarantees

在现有 `handoff.py` 增加：

```text
prepare --handoff <core> --mode <mode>
finalize --handoff <core> --observation <bounded-proof.json>
admit --handoff <core> --attestation <bounded-attestation.json>
retention archive|restore|reopen|purge --handoff <core> --confirm-handoff-id <id>
```

`prepare` 默认 `core_only`，只验证 core 并记录 intent，不调用远端。`finalize` 只验证 bounded observation，不写远端，
不 read Plugin state，不无限重试。`admit` 重新 validate core，记录协调器已经完成完整 prompt 阅读、
`$trellis-start`、current-fact reconciliation 的有限声明；该声明不是密码学证明，也不授权继续执行。
它不能伪造 target pointer，也不能把 source session 的 fallback pointer 当作 target identity。

模式：`core_only` 默认；`capsule_required` 需要已授权 create/write 的 exact-read digest；
`archive_required` 要 boundary/source-session/archive proof；`convergence_required` 再要 Task completed、
completion artifact 与 memory diff。当前未通过 disposable fixture/W4 的远端观察必须 `unsupported`/
`unavailable`，不使用 HTTP fallback 或自然语言 recall 填补。

## Boundary and retention

延迟 finalizer 必须重新通过现有 `_verify_rollout`，要求原 inode/prefix 仍可读；或由未来独立合同
提供 bounded sealed-boundary receipt。不得放宽 rollout 校验或复制 transcript。官方 Plugin 是唯一
transcript catch-up/commit 执行者；finalizer 只是 source 进程外的短命观察器。

`archive`：resolve exact core -> validate -> 只枚举 core/prompt -> temp copy -> hash/size/regular-file
verify -> fsync/rename -> append event。canonical package 默认保留，所以旧 validator 继续可用。`purge`
仅在 exact confirmation+verified archive 后先 append purge intent、再 unlink canonical core/prompt；sidecar 留作审计。restore/reopen
只恢复同 id archive，存在不同内容即拒绝；restore 以 archive 的严格 core schema/payload digest 校验为依据，不依赖旧会话的 Git/evidence 仍未漂移。任何失败不删 source。

## Code placement

- `workflow_contracts.py`：共用 bounded event/observation validators/digests；
- `handoff.py`：复用 `_root`, `_destination`, `validate`, `_atomic_json`，添加 receipt reducer/CAS/retention；
- `render_handoff_prompt.py`：保留 ready gate，仅增加 mode/receipt 的有限说明；
- `SKILL.md`：明确 source wait、target stop、core-only fallback、retention 与官方观察；
- `pennix-workflow-routing`：仅更新所有权和停止条件。

不创建新的 Skill/Hook/worker，不重写 rollout parser，不添加 OpenViking client。

## Failure and rollback

core drift 仍为 `changed`；source 未结束为 `pending`；管理面不支持为 `unsupported`；target 未核对为
`not_admitted`；copy failure 不改变 retention；sidecar chain 断裂为 `failed` 但不影响 core validate。
回滚使用先前 Pennix Skills commit/安装器；不删 task/handoff/rollout/remote data/cache。
