# 适配 Context Mode v2 消费方与评估

## 目标（Goal）

执行根任务 context-mode-routing-upstream-audit 已批准的 W2。以 Context Mode v2 上游实际设计替代强制默认调用要求，消除失效 Skill 路径与旧数据清理合同。

## 需求（Requirements）

- 删除 pennix-context-mode-integration 集合成员及实际引用，不保留空壳或改名迁入。
- 路由尊重宿主原生输出处理；大输出分析按需使用 Context Mode，原生工具允许逐次回退，拒绝不得绕过。
- 路径严格使用宿主声明的物理路径与别名映射，不猜测扁平位置。
- 清理说明适配 v2 shared project、journal 与上游保留策略；安装仍由 Lifecycle 负责。
- 评估固定 before/after 来源并分别报告文档检查、真实调用与无法覆盖项；不伪称压缩或成功读取。

## 验收标准（Acceptance Criteria）

- [ ] collection verify 与受影响路由、评估测试通过，集合不包含被移除成员。
- [ ] 受影响静态评估、真实 before/after 及路径场景有可核验结果。
- [ ] 固定公开提交供 Lifecycle 消费，安装集合经 owner 移除旧成员。

## 备注（Notes）

- 修改目标仅本组件源码、测试与任务资产；不直接编辑安装副本、凭据或其他组件。
- 用户已明确授权最终复核后实施和收敛；本任务为该已展示并批准方案的同范围组件落点，不是新的独立需求。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"upstream-first","status":"decided","question":"集成成员与路由如何取舍","evidence":["根任务 design.md：G6、G8 及 implementation-approval.md"],"answer_or_reason":"移除独立集成 Skill，遵循 v2 上游和宿主行为；命令归 CM/Lifecycle，原生工具可回退。","impact":"manifest、路由、清理与评估。","reopen_when":"发现改变范围或验收的新重要用户取舍。"}]}
```
