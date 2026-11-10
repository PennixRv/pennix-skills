# 全量 Skills 场景路由与评估适配

## 目标（Goal）

执行根任务已批准合同 WP1/WP3：主集合路由、两集合身份及真实行为评估；用户当前整体批准覆盖本包。

## 需求（Requirements）

- 执行根任务 `11-10-pennix-skills-scenario-routing` 已接受的 design/implement 合同 WP1/WP3，保持 main 分支。
- 在现有总路由维护 25 项业务场景与五阶段连接；直接匹配优先，不新增调度器或第二清单。
- 扩展既有评估器的双集合身份、案例能力与恢复预算证据；原始记录只留私有临时目录。

## 验收标准（Acceptance Criteria）

- [ ] 集合 verify、路由引用和相关单测通过。
- [ ] 两集合身份漂移、首读失败、案例权限、模型轮次预算有有效验证。
- [ ] 固定提交推送，原生安装后真实场景及恢复验收由根任务记录，本组件不以静态结果宣称整体完成。

## 备注（Notes）

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"scenario-routing","status":"decided","question":"全量方法触发与真实验收方案","evidence":["根任务 design.md、implement.md、implementation-approval.md"],"answer_or_reason":"用户已批准原生直接匹配、现有总路由、25项覆盖、正式发布安装与61次场景验收；本组件落实WP1/WP3。","impact":"总路由、既有评估器及相关测试。","reopen_when":"范围、权限、预算或验收合同发生实质变化。"}]}
```

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
