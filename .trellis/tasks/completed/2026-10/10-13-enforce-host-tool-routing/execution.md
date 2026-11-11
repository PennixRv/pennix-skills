# 实施与验收

## 已完成源码

既有唯一 `AGENTS.md.install` 工具规则已调整为明确禁令和原生调用义务，未新增并行规则，未扩写 Grill/routing 正文。对应路由合同测试通过 8 项。模板 SHA-256 为 `d075aafd70b6a0408672421245fa3feaf03c5a6f358ff6755700733e2e03be91`，catalog 的 codex-agents revision 已同步。

中文写作 Skill 与 workflow-assets 参考已区分机械合同、稳定英文锚点和 owner 批准的源模板自然语言；写后复核分别落到中文校对与人工事实复核、英文锚点字面核对、Trellis 解析/生成/冲突测试。未新增英语语法门禁。中文 linter 的 22 项测试通过，本次明确的文案检查无 error 或 warning；样式建议按本集合约定人工判断。

安装预检识别到当前完整旧 AGENTS 的摘要尚未列入 legacy 允许集合。按现行机制补入 `819d4dca89d346d3e8bfb5b8fe26702dee5ddc10ed69cc62293f0b97a5d6a281`，夹具来自本仓库 `5bb372b` 的受跟踪源模板，绝不来自用户运行态。既有参数化回归覆盖精确旧版升级和漂移拒绝，lifecycle 176 项通过。

待 Trellis beta.47 实际发布后更新 approved pin，复验 catalog 合同并提交推送。然后使用系统 skill-installer 完整相邻暂存安装、新入口 replace-staged、显式 codex-agents 和 trellis-cli upgrade/verify，不手改用户资产。模板安装不能自动证明宿主模型行为；无受支持行为评估入口时明确保留此限制。

## 发布 pin

Trellis CLI 与 Core 的 beta.47 已通过原生 `release-preflight verify-npm --package all`；首次 CI 仅在 registry 传播核验超时后失败，随后本地核验成功，已原生重跑可重入的发布门禁。catalog 的 `trellis-cli.approved_version` 更新为实际 `0.7.0-beta.47`，不凭标签猜测可安装版本。

## 安装与最终验收

源码提交 `67e7037` 已推送实施分支及 main。Trellis 发布 CI 原生重跑成功。系统 skill-installer 从已推送来源完整安装 catalog 声明的 12 项 Skill 到相邻暂存目录，再由暂存集合的原生 `replace-staged` 事务替换活动集合；新 lifecycle 入口随后执行 `codex-agents` 和 `trellis-cli` 的原生 upgrade。未手改安装副本。

| PRD 验收项 | 实际结果与证据 |
| --- | --- |
| 唯一模板规则 | 既有规则调整为精确禁令和宿主已声明工具的原生调用义务；保留可用性与失败合同，不重复扩写 routing 或 Grill。 |
| 合同测试与精确落点 | routing 8 项、lifecycle 176 项、中文文案 linter 22 项通过；catalog 的 AGENTS SHA-256 为 `d075aafd70b6a0408672421245fa3feaf03c5a6f358ff6755700733e2e03be91`，Trellis approved version 为实际 beta.47。 |
| 文案与行为边界 | 两份中文写作资产已完成文案与事实复核，未增加英语语法门禁。静态合同测试和物化检查不能保证模型每次遵守；没有受支持的宿主行为评估入口，不声称已证明该行为。 |
| 提交、推送及原生部署 | 12 项集合完整替换，暂存状态为 none；`codex-agents`、`trellis-cli`、`pennix-skills` 的独立 verify 均为 match，failures/advisories 均为空。`discover` 识别 AGENTS 为 current 且 active，无 override 遮蔽。用户 AGENTS 与唯一源模板字节一致，宿主已重新加载该规则；CLI 实际为 `0.7.0-beta.47`。 |

以上证据满足本任务验收；已封口的规划文档保留批准时原文，完成状态由本记录与原生归档表达。原始部署回执保留于本机临时目录，仅将必要结论写入任务，不提交用户运行态。
