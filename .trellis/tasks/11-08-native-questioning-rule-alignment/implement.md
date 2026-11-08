# 有序实施计划

1. 复核三个 Skill 和引用，按根合同作最小语义修改；保留全部权限、停止和归属边界。
2. 复用 eval 来源/认证/摘要，加入原生 app-server 问答入口及有意义的协议测试；保留 exec 用例。
3. 运行 collection、相关测试和中文内容检查，核对差异后提交推送；不得 amend。
4. 根任务经 Lifecycle 物化固定提交，进行真实 before/after 模型评估，失败保留并修复受影响范围。
5. 原生记录结果与任务归档，单独提交收尾资产；根任务固定最终提交并验收实际安装。

依赖：用户完整授权已取得；真实评估需固定公开提交及真实 owner receipt。唯一正常停止点见 design.md，不将单元测试或提交完成等同于整体完成。

<!-- trellis-implementation-plan:v1 -->
```json
{"schema_version":1,"steps":[{"id":"rules-evaluation","target":{"repository":"PennixRv/pennix-skills","branch":"main","component_or_path":"三个相关 Skill、必要引用和 evaluations"},"depends_on":[],"action":"按正文步骤 1–3 修改规则和评估，检查后提交推送。","deliverables":"规则差异、交互入口与测试、固定公开提交。","verification":"collection、相关合同与评估单元测试。","risks":"遗漏原约束、错误回退或用 fixture 冒充模型行为。","rollback":"只撤回本任务差异，安装由 Lifecycle owner 恢复。"},{"id":"delivery","target":{"repository":"PennixRv/pennix-skills","branch":"main","component_or_path":"评估记录与任务收尾"},"depends_on":["rules-evaluation"],"action":"由根任务固定来源物化并实测，按正文步骤 4–5 汇总和归档。","deliverables":"审阅后的行为摘要及完成任务记录。","verification":"固定来源、真实协议/模型和根安装验收。","risks":"未测的必需项不能报告通过。","rollback":"失败保留，修正新提交，不覆盖公开历史。"}],"stop_point":{"condition":"组件交付、owner 安装和根验收全部完成。","observable_evidence":"公开 SHA、真实归属摘要、模型与集成结果。","remaining_work":"满足后无本组件剩余；未满足记录精确断点。"}}
```
