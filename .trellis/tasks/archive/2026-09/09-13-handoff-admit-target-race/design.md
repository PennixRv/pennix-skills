# 设计

## 不变量

1. core 是不可覆盖的导航资产：稳定 `handoff_id`、可解析 JSON、成对 prompt 和原子发布足以界定它；当前
   Trellis/Git/文件事实由 target reconciliation 核对，不由 capture 时的 digest 断言。
2. admission 是 receipt 内的单一成功提交：调用先读取 core/prompt，再核对 direct target、Trellis start 和
   facts attestation；持有既有 per-handoff `flock` 时复查成功 target。同 target 返回幂等，其他 target 拒绝。
3. receipt 仅记录 source、target、retention 三个状态轴及可读 evidence refs。它不是第二套任务账本，也不以
   hash chain、固定大小或自定义权限证明模型理解。
4. Trellis ownership 的 `core_digest` 是其现有 API 的内部身份参数。helper 仅在调用该 API 时按现有接口计算，
   不把它写入 core/receipt，也不将其解释为语义可信度或消费完成证明。

## 兼容与恢复

- 新 core 使用无摘要的 schema 6；schema 4/5 仍按路径、类型和必要字段读取，忽略其历史摘要字段。
- 新 receipt 不含 digest 链；旧 v1 receipt 只读取其公共状态字段，使已存在资产可以继续 `status`、retention
  或 admission，而不把历史摘要再次作为门槛。
- core/prompt 未发布或不可读时 admit 失败且不写成功事件；进程中断前可重试，写入后同 target 读取状态即幂等。
- archive 保留原子 copy/replace，复制后仅确认 core 可解析、prompt 可读；不以文件摘要比较或阻止恢复。

## 不做

- 不改 OpenViking、Trellis ownership 源码、Plugin、远端数据或任务指针。
- 不增后台调度、hash/CAS、长度配额、可信度阈值、权限模型或第二份 ledger。
