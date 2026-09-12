# 收敛 handoff 生命周期与 target admission

## Goal

将已发布实现收敛到已批准的 handoff 合同：receipt 的同一 per-handoff 锁内只允许一个
`reconciled` target；交接入口明确要求完整读取配对 JSON core 与 prompt；删除旧投影遗留的摘要、固定容量、
静默截断和快照漂移准入门槛；补定向回归测试并发布重装。

## Requirements

1. `lifecycle_admit` 的“已成功消费 target”判断必须在 `_append_event` 持有的同一 per-handoff
   `flock` 内再次执行，不能只依赖锁外预检。
2. 两个不同的 current direct target 并发提交完整 admission 时，只允许一个写入
   `target_status=reconciled`；另一个必须得到明确的已消费错误，不能追加第二个成功 event。
3. 同一 target 对已经成功的 admission 重试仍返回幂等结果；不完整 admission 仍不构成消费。
4. 不改变 Trellis ownership、OpenViking、长度/置信度策略或 archive 的职责边界；handoff core/receipt 可为
   删除旧摘要门槛而升级 schema，但必须保留旧 schema 的读取兼容。
5. 生成的短入口与配对 prompt 都必须明确：receipt `ready` 后完整读取配对 JSON core 和 prompt，才可进入
   `$trellis-start` reconciliation；不得把读取 prompt 单独表述为完整消费。
6. 新建 core 不得再写入或验证 payload/source/evidence/rollout 的 SHA-256 字段、snapshot digest、固定文本/
   候选/记录/receipt 容量上限或截断。schema 4/5 的既有 package 仍可解析，但其旧字段不能成为新 `ready`、
   consumption 或 lifecycle 的门槛。
7. receipt 保留原子 JSONL 状态历史和三个独立轴，但不得再形成 digest 链或把 digest 作为消费完整性的证明。
   仅 Trellis ownership 原有 `--core-digest`/CAS 接口可以使用其既有 digest，不回写进 core 或 lifecycle receipt。

## Acceptance Criteria

- [x] 新定向并发测试稳定复现两个不同 target 的竞争，并断言仅一个成功、receipt 只含一个 reconciled admit。
- [x] renderer 测试断言短入口和配对 prompt 均要求读取 JSON core 与 prompt。
- [x] 定向测试证明新 core、receipt 和 observation 不含 handoff SHA/容量门槛；长 capsule/rollout 不被截断，
      source/evidence 后续变化不阻断 `ready`，legacy core 仍可读取。
- [x] 现有 handoff、renderer 与安装器测试通过，且静态 Skill 校验通过。
- [x] 修改仅限 handoff helper 和对应测试；源仓库提交推送后由官方安装器重装，并核对安装副本。

## Notes

- 用户已授权本轮修复、推送和重装。
