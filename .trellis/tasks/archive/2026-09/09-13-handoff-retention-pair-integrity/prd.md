# 保证 handoff retention 保留成对资产

## Goal

修复已 admission 的 handoff retention archive 对 paired prompt 可选处理，使归档、恢复和状态读取不接受只含 core 的不完整资产；补最小回归，发布并官方重装。

## Requirements

1. 仅当 canonical handoff JSON 与其可读的 `session-handoff-prompt.md` 都存在时，`retention archive` 才能
   建立 archive。prompt 缺失、符号链接、非普通文件或不可读时必须报 `ContractError`，不能产生只含 core 的
   archive 或写入 `retention=archived`。
2. 既有 archive 也必须是完整 pair：archive snapshot、restore、reopen、purge 和 canonical 已不存在时的
   `status` 均拒绝只含 core 的 archive。拒绝不得改写 receipt、替换 consumer、重复 admission 或执行 pending action。
3. 修复后，补回 canonical prompt 再次运行 retention archive 必须成功；同一 target 的 successful admission
   仍为一个，retention 继续是独立、可重试状态轴。
4. 复用现有 `_regular_file` 和 `_archive_snapshot`，不新增 schema/event、digest/hash、长度限制、权限模型、
   后台流程或 OpenViking/Trellis 调用。新 core、旧 schema 读取和正常 archive/purge/restore 行为不得回归。
5. 修改必须限于 `pennix-session-handoff` 的 helper 与定向测试；完成后运行组件全量测试、安装器检查、发布
   `origin/main`，再使用官方安装器重装并核对运行时资产。

## Acceptance Criteria

- [x] 回归证明已 admission 后移除 canonical prompt 时 archive 失败、receipt 保持 `archive_eligible`、不存在
      不完整 archive；补回 prompt 后 archive 成功且 successful admission 仍为一。
- [x] 回归证明 archive prompt 丢失时 `status` 与 `restore` 拒绝该不完整 archive，且不产生额外 lifecycle event。
- [x] 正常完整 pair 的 archive/purge/restore、legacy core、single-target admission 和 renderer 行为保持通过。
- [x] `pennix-session-handoff` tests、安装器 tests、`py_compile`、`install.py --check` 和差异检查通过。
- [x] 源码提交推送后经官方安装器重装；安装副本中的运行时 `SKILL.md` 与 handoff scripts 和源一致。

## Notes

- 用户已明确授权本轮修复、提交、推送和重装。安装副本、OpenViking/Trellis/Plugin/NAS 和 root task 不是
  组件源码修改目标。
