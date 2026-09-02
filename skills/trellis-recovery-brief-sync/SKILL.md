---
name: trellis-recovery-brief-sync
description: "仅当当前项目存在有效活动 Trellis 任务，且主协调器位于已批准的任务激活、已核验实质语义变更、正式交接/暂停/完成/归档或用户明确请求的闸门时，使用此 Skill 同步受控 RecoveryBrief。不得用于普通编辑、测试、差异、压缩、普通恢复或工作节点。"
---

# Trellis RecoveryBrief 协调

此全局私有 Skill 为已初始化 Trellis 项目的主协调器提供受控的 RecoveryBrief 同步协议。
Codex 原生压缩负责当前对话线程的压缩；Trellis 的当前活动任务及其可信材料是唯一项目
语义事实；context-mode 只提供 `ctx_recovery_brief_*` 的状态读取与原子比较交换协议。本 Skill
不会执行压缩、选择 provider、改变压缩路由或提供远程压缩失败的动态回退。

## 适用前置条件

开始前先在当前工作目录确认下列条件，任一条件不满足即报告“当前项目不适用”并停止：

1. 当前目录属于一个项目根目录，该根目录存在 `.trellis/`。
2. 项目的当前任务入口可以解析出有效活动任务；从子目录执行时先定位项目根目录，再使用该
   项目提供的 `task.py` 接口。
3. 调用者是主协调器，且当前动作处于本 Skill 的批准闸门。

前置条件失败时不得调用 `ctx_recovery_brief_status`、`ctx_recovery_brief_update` 或其他
`ctx_recovery_brief_*` 接口，不初始化 provider，也不写入任何状态。不要在
`/home/penn/.codex` 初始化 Trellis。

## 批准闸门

只在下列时点执行 status-first 协议：

1. 经批准启动任务后、第一项实施工作前。
2. `trellis-check` 已确认实质语义变更，且该变更已经记录到活动任务的可信材料后。
3. 明确的交接、暂停准备、完成或归档之前。
4. 用户明确要求检查、修复、强制刷新或正式交接时。

普通编辑、测试、差异检查、常规压缩、`PreCompact`、`PostCompact`、`SessionStart(compact)`、
checkpoint `claimed` 与普通恢复均不适用。它们只传递当前会话线索或执行结果，不能单独建立
新的项目语义事实。原生远程压缩失败、为修改 provider 或压缩路由而完整重启 Codex、以及新会话
刚恢复也不构成闸门：不得调用本 Skill 伪造 local 回退、写入人工任务状态或以会话摘要替代
Trellis 事实。工作节点只交付其分配的运行时报告，不得调用本 Skill 或刷新 Brief。

## 同步协议

1. 对当前归属会话直接调用 `ctx_recovery_brief_status`。
2. 若状态选择有效活动 Trellis provider，且现有 Brief 可用、未漂移并已表示当前确认事实，
   只报告无内容的状态结论，不写入。
3. 若 Brief 缺失或漂移，只读取当前活动任务适用的可信 `task.json`、`prd.md`、`design.md`、
   `implement.md` 与 `check.md`。会话文本、FTS 结果、原始工具输入输出、完整工件正文与 Git
   差异均不是事实源。
4. 构造完整而精简的 RecoveryBrief。每项事实使用 `source_kind: "trellis_task"` 与当前状态的
   `trellisSourceSha256`；不得包含凭据、个人信息、原始工具数据、会话文本、完整任务正文、
   Git 差异或未核验检索结果。
5. 调用 `ctx_recovery_brief_update`，其 `expected_sha256` 必须等于状态返回的 `briefSha256`；
   只有状态明确没有 Brief 时才使用 `"absent"`。仅报告无内容的更新结果，再读取一次状态确认。

## 错误处理

- `TRELLIS_SOURCE_DRIFT`：重新核验已变化的活动任务材料，使用新的 `trellisSourceSha256` 与
  旧状态的 `briefSha256` 刷新。不得投影或重建过期 Brief。
- `CAS_CONFLICT`：重新读取状态、重新评估当前 Trellis 材料，仅以新返回的 Brief hash 重试。
- `TRELLIS_RUNTIME_INVALID`、`TRELLIS_TASK_INVALID` 或 `TRELLIS_BRIEF_INVALID`：先修复
  Trellis 状态；不得用项目 provider 绕过失效 Trellis 指针。
- `NO_PROVIDER`：本 Skill 不初始化项目 provider。只有没有 Trellis 指针且用户明确要求
  项目局部 provider 时，才在本 Skill 之外按其专用流程处理。
- Codex 原生远程压缩失败：这不是 `ctx_recovery_brief_*` 的协议错误，也不是本 Skill 的调用
  条件。保留活动 Trellis 任务与已核验状态；如确需改变后续会话路由，按真实配置或 provider
  流程处理后完整重启 Codex，并在新会话按 Trellis 恢复。不得把
  `remote_compaction_v2=false` 当作强制 local 或离线后备开关。

## 所有权边界

- 只有主协调器可执行本协议。主协调器独占任务事实、验收结论和 Git。
- checkpoint Hook 保持其自身的失败开放行为，不调用本 Skill、不写 Brief、不修改 Trellis
  任务材料。
- 本 Skill 只提供有界恢复上下文；不会决定压缩后如何继续对话、替代原生压缩或动态故障切换，
  也不替代项目自己的 `.trellis/workflow.md`、`AGENTS.md` 或任务规则。
