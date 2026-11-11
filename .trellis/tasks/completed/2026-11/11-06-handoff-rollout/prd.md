# 修复交接 rollout 精确定位

## 目标（Goal）

根任务 11-06-rollout 已批准的交接定位修复；只读精确线程元数据查询、文件身份验证、Skill 指引、回归与发布。

## 需求（Requirements）

- 实施根协调任务 `11-06-rollout` 已接受并由用户明确答复“同意”的方案：在现有 handoff CLI 增加只读 resolve-rollout，精确查询当前 CODEX_THREAD_ID 对应元数据并校验文件身份；Skill 使用此入口准备请求。
- 不猜日期、不扫描会话、不写 Codex 数据库、不新增 Hook/依赖、不改变 schema 12。保留显式 path 合同与无任务退出码处理。
- 组件 main 分支交付代码、测试和规范；根仓固定发布 commit，pennix 原生更新安装。现有根 design.md 为用户批准内容，本组件资产只作相同范围的本地展开。

## 验收标准（Acceptance Criteria）

- [ ] 精确解析跨日与归档路径；无身份、无记录、结构不匹配、无文件、符号链接或会话身份冲突均受控拒绝。
- [ ] 新测试先红后绿，完整 handoff 测试、集合校验与当前线程只读探测通过。
- [ ] 提交推送 main 后，根任务通过 pennix update 安装并验收精确 commit。

## 备注（Notes）

根方案批准 revision：`ce9049d6d437c686ad608ab90f62b05292a760d5135ffc83bcbd71344e464172`；实施授权引用：根任务 `approval.md`。根任务已进入 task_implementation；不重复索取同范围授权。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"resolver","status":"decided","question":"如何避免猜测当前 rollout 路径？","evidence":["design.md","根任务 11-06-rollout/design.md 与 approval.md"],"answer_or_reason":"用户同意只读精确元数据解析并验证文件身份；保持既有显式路径合同。","impact":"只改交接 CLI、Skill、回归和对应规范；发布与安装沿原生 owner。","reopen_when":"元数据不可用或发现改变授权范围的事实时停止相关动作。"}]}
```

- 让 `prd.md` 聚焦需求、约束和验收标准。
- 轻量任务可以只保留 PRD。
- 复杂任务在 `task.py start` 前增加 `design.md` 记录技术设计，增加 `implement.md` 记录执行计划。
