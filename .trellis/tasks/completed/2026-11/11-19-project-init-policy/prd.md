# 说明原生项目自动初始化授权边界

## Goal

承接根任务 project-init-trust-automation 已批准P4；更新原生自动初始化、Lifecycle一次策略和CodeGraph项目边界说明，验证集合并交付固定提交。

## Requirements

- 根任务 project-init-trust-automation 已由用户整体批准并进入原生实施路线 revision 2；本组件只承接 P4 的原生入口和一次策略说明，不扩大索引或系统操作授权。
- 说明主动 Trellis Codex 初始化可承接 Lifecycle 已明确开启的策略，不由 Agent 重复串联或逐项目重新询问；明确拒绝、修改资产、未知配置仍保留。
- 原生查询不触发初始化；CodeGraph 新项目边界、禁止 Git Hook 回退和严格状态由原生 help／MCP 拥有，不复制协议。

## Acceptance Criteria

- [ ] 集合 verify 及适用静态合同检查通过；普通查询不被写成自动索引触发器。
- [ ] 交付 main 固定提交供 Lifecycle 物化；本任务原生完成，根任务负责最终两机及集成。

## 验收覆盖

| 接受条件 | 工作包 | Owner | 验证入口 | 交付证据 | 停止条件 |
| --- | --- | --- | --- | --- | --- |
| 原生策略与项目授权一致 | P4 | Pennix Skills | collection verify、引用及边界审查 | execution.md | 第二执行器或默认索引 |
| 固定来源交付 | P4 | Pennix Skills | main／远端及原生归档 | 最终提交 | 来源漂移 |

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
