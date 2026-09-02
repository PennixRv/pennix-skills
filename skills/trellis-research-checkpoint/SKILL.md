---
name: trellis-research-checkpoint
description: 在活动 Trellis task 中开展会产生事实、候选或结论依据的研究、审计或只读调查时使用；要求在当前上下文窗口及时落地 checkpoint，并按风险决定是否需要独立反审查。普通导航、重启、压缩和正式交接不触发。
---

# Trellis Research Checkpoint

将任务相关研究落地到当前 Trellis task，避免结论只留在可压缩的对话上下文。当前字段、风险阈值、失败闭合和验证要求以
`.trellis/spec/operations/workflow-governance-current.md` 为准；本 Skill 只负责路由，不创建独立任务事实源。

## 何时使用

先按下表决定；详细字段、风险与失败闭合始终以
`.trellis/spec/operations/workflow-governance-current.md` 为准。

| 当前动作 | 必须动作 |
| --- | --- |
| 单次导航、无任务价值的短小观察、普通重启、压缩、等待、验收失败或 RecoveryBrief | 不创建 checkpoint，也不授权 `$trellis-session-handoff`。 |
| 活动 task 的研究、审计、资料核验或候选报告产生事实、候选、不确定项或下一步决策依据 | 在继续无关研究、扩大范围、派发高影响工作或结束当前窗口前记录 checkpoint。 |
| 局部、可逆且不触及安全/权限/生命周期/跨组件根因或外部易变事实的结论 | 记录 checkpoint，并以 `review_policy={mode: exempt, risk: low, reason: ...}` 说明豁免。 |
| 其他结论，或任何高影响边界 | 记录 checkpoint，并通过 `parallel-work` 请求 required 独立反审查。 |

## 工作顺序

1. 确认当前活动 task、实际修改目标和当前事实源；先本地核验检索或 worker 结果，不能把候选直接写成事实。
2. 通过 `$trellis-document-governance` 在当前 task 的 `research/` 或适当任务工件记录 checkpoint：范围、问题、时间、
   带 evidence locator 的已核验事实、与事实分开的 candidates、未决项、一个有界下一动作和禁止重复动作。
3. 对高影响结论，使用 `parallel-work` 请求独立的第二视角，并声明
   `review_policy={mode: required, risk: major|critical, reason: ...}`；主会话在 runtime collect/verify/accept 后核对独立
   `review_lens`、`review_of`、`evidence_refs`、`review_verdict` 和 coverage，才可接纳结论。
4. 若 gate 为 `insufficient_independent_review`，或证据关系无法核验，保留事实与缺口以及一个有界下一动作；不得提升候选、
   修改 Issue 状态、无界重派或继续依赖该结论实施。

## 边界

- Trellis 是 task/checkpoint 的唯一事实源；context-mode、会话摘要、RecoveryBrief、prompt 和 worker 报告只提供线索或候选。
- `parallel-work` 只在独立并行候选工作或反审查确有证据价值且当前用户请求/任务已授权时使用；活动 batch 期间主会话
  停止依赖其结果的实施，按 Trellis channel 的单等待者和收集协议推进。
- 本 Skill 不修改 Trellis fork、cache、Hook trust、任务生命周期或正式 handoff；不复制 runtime ledger、对话、
  凭据、配置正文或原始大输出。
