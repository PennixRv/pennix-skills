# 物化 Windsurf owner 凭据新版并对齐导航

## 目标（Goal）

根 converge-pennix-lifecycle 已授权：按 collection.json npm-pack 物化真实 Windsurf 已发布提交，验证源身份、集合及受影响导航，提交消费版本。

## 需求（Requirements）

- 沿根 converge-pennix-lifecycle 已批准合同 WP3，只更新 collection.json 固定 Windsurf 真实源与原生 npm-pack 物化结果及相关导航。
- 不直接编辑物化源码，不引入中央凭据或部署执行器；发布、安装和备份处置由根协调。

## 验收标准（Acceptance Criteria）

- [ ] 声明提交与完整物化字节一致，collection verify 和受影响测试通过。
- [ ] 源提交推送后由 lifecycle 固定消费，原生任务收尾。

## 备注（Notes）

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"source","status":"decided","question":"物化源与部署边界","evidence":["根合同 WP3；user-approved-implementation-2026-11-07"],"answer_or_reason":"先发布真实 Windsurf 源，再固定完整提交并原生 npm-pack 物化。","impact":"collection.json、生成快照和导航。","reopen_when":"源发布或现有物化机制未通过验证。"}]}
```
