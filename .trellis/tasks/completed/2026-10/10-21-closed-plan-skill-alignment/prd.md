# 对齐 Trellis 封口方案的用户级技能路由

## Goal

修复 Trellis 状态机变更后 `pennix-skills` 中已证实的协作缺口，使用户级技能正确委托项目规划入口，保留各组件的职责。根协调任务为 `codex-workflow-optimization/.trellis/tasks/10-21-idea-to-closed-plan-state-machine`。用户明确要求本次查漏补缺在当前任务内完成，不构成 replan。

## Scope

单一文档行为修复：`pennix-decision-grill`、`pennix-workflow-routing` 和 `pennix-agent-output-quality` 的 Trellis 委托、方案展示说明及受影响的合同测试。全量检查集合中的 Trellis 相关引用；其余技能若接口未受影响，只记录核对结果。决策提问方法及非 Trellis 项目的方案审阅保持可用，不复制 Trellis 阶段表或材料 schema。

## Verification

- Trellis 项目由宿主声明的 `trellis-idea-to-closed-plan` 负责方案形成、详细有序步骤、唯一可观察停止点、审查、展示和原生封口批准；用户级技能不维护另一套顺序或省略 digest 参数。
- 删除“replan 仅允许 in_progress”的旧断言；模型负责变化分级，minor 记执行台账后原阶段继续，major 委托项目入口选择合法原生回退并重新批准。
- 集合 verify、受影响的决策合同测试、集合完整测试和 Skill 校验通过；明确静态测试不证明模型行为。
- 本地提交源码并由根固定 gitlink，原生归档 owner task。停止点不包括安装集合替换、发布或 push。

## Rollback

变更仅在 `pennix-skills/main` 源码工作树完成，可按本任务前提交 `4d95220` 恢复；不写安装副本或运行时配置。出现重要未决选择时先暂停相关改动，沿根任务的用户决策合同处理。
