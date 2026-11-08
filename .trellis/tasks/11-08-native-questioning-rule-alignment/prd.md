# 修复原生提问判断与 Skill 联动规则

## 目标（Goal）

实施根任务已批准合同的 Skills 工作包：提问入口、v2 路由、Tavily 请求前回退和真实交互评估；根合同及授权为上游依据。

## 需求（Requirements）

- 遵守根任务已批准合同 `../.trellis/tasks/in_progress/11-08-native-questioning-agents-optimization/design.md`；该路径从本仓库根解析。用户明确批准组件提交推送、Lifecycle 发布、安装与验收。
- 修正同步工具直接声明与嵌套工具清单的混淆，保持异步行为禁令和真实宿主用途限制。
- 对齐 decision-grill、routing 和 Tavily 的 v2 路由及请求前本地失败回退，不放宽权限拒绝或请求后错误的停止边界。
- 补充真实 app-server 交互与模型评估，复用来源校验和认证命令；秘密、原始会话和运行态不入 Git。

## 验收标准（Acceptance Criteria）

- [ ] 三个 Skill 与必要引用一致，无错误路径推导、旧强制 Context Mode 表述或非法重试。
- [ ] collection、相关单元与评估测试通过，真实行为结果由根任务汇总，不以静态检查代替。
- [ ] 固定提交公开可取，Lifecycle 物化来源与之吻合；完成本仓库任务收尾。

## 备注（Notes）

- 本仓库未更新的 Trellis 原生接口仍使用 plan seal/approve/archive；按实际接口记录组件状态，不修改工作流或模拟根仓五阶段协议。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"approved-root-contract","status":"decided","question":"本组件如何落实用户规则与提问优化","evidence":["根任务 design.md、review.md、implementation-approval.md"],"answer_or_reason":"用户明确批准完整方案及组件提交推送、Lifecycle 发布安装和验收收尾；本组件落实 Skills 与评估。","impact":"三个相关 Skill、必要引用和有界交互评估。","reopen_when":"范围、依赖、权限、成本或验收出现实质变化。"}]}
```
