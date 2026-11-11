# 用户 Skill 共享发现入口实施

根协调任务已经完成需求、用户选择和整体方案批准，用户明确纠正本任务属于实施任务。按根任务 `implementation-contract.md` 执行，不重复索取已给授权。本组件只负责用户集合路径规则与既有行为评估的适配，由当前会话实施。

验收要求：声明路径保留集合层级，用户集合指向 HOME 的 `.agents/skills`，CODEX_HOME 只负责宿主配置；评估绑定真实 collection target、receipt、完整提交及树摘要，配置与 provider 分离；首次失败、相对引用、主/extra/项目边界及原生恢复证据保留。不得新增 Skill、注册表、执行器或复制认证。

源码修改限 `pennix-workflow-routing`、既有 evaluation harness 和相关测试/spec。先执行领域测试，再集合验证和实际宿主评估；部署由 Lifecycle 固定本组件提交，原生正式安装、真实恢复及根集成在根任务完成后再归档。重要边界失败保留现场，禁止设计结案替代实施交付。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"shared-root","status":"decided","question":"用户集合布局及验收强度","evidence":["根任务 design.md、solution-evidence.md、implementation-authorization.md"],"answer_or_reason":"用户批准保留集合层级、HOME 共享入口和流程与行为验收；当前组件实施既定落点。","impact":"routing、评估来源及测试。","reopen_when":"发现改变既定范围、授权或验收的重要事实。"}]}
```
