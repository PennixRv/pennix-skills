# 优化用户级 AGENTS 模板与分层验收合同

## Goal

保留稳定的 Pennix 全局协作原则，精简用户级工具可用性规则的低层重复，补全及时留痕和局部范围说明，并安全更新模板源、验证和本机分发。当前只规划，受保护目标未获后续批准前不修改。

## Requirements

1. 模板工具规则保留宿主声明/真实回执、`functions.exec`/`ALL_TOOLS` 一个必要反例、原错误和 owner 合同；完整失败分类、容量/续读由既有 owner Skill 承接。
2. 决策段增加一句“围绕小目标及时把关键结论、决策和进度写回已有自然落点，尽量在当前窗口留痕”；继续/压缩恢复合同保持，复用 Trellis 已有产物，不新建日志。
3. 职责段明确具体项目和目标目录适用的更具体规则及选定工作流；系统部署与项目初始化的授权边界清楚。
4. 更新 catalog 的模板 SHA，将当前完整发布模板 `c73dd09cb6fd26f2b31b286673a73251eb5a900625bb1e1b07f1ceb51a848326` 加入精确 legacy 摘要，沿既有原子替换和漂移阻断升级；不引入旧语义兼容功能。
5. 同步 workflow routing 的模板合同断言，以及 lifecycle 的精确旧版迁移测试和夹具；不把模型行为保证写成字符串测试。
6. 通过组件质量门，提交至 `task/optimize-user-agents-template` 并合 main 推送；用系统 installer staging 与 lifecycle 在隔离目标验证后更新本机。Extra 源码、pin、白名单与专项 Skill 算法没有当前必改证据，保持相关短交接规则。

## Acceptance Criteria

- [ ] 全局稳定原则、必要反例及条件不丢失，完整错误细节归既有 owner；不设人为行/字节长度门槛。
- [ ] 自然留痕、继续恢复及局部规则边界可理解且无冲突，无新增台账/自动知识写入。
- [ ] 模板、catalog revision 和合同测试一致；当前已发布完整模板可升级，个人漂移或未知内容仍拒绝且原文保留。
- [ ] lifecycle、routing、FastCtx、Grill 相关既有测试和 `git diff --check` 通过。
- [ ] 已推送提交可核验，原生接纳与隔离/本机物化完成；源与目标字节一致、有效来源未遮蔽，两套集合保持独立。
- [ ] 本组件当前封口修订得到展示之后的明确批准；主会话原生 approve/start 后才实施，验收证据和 Git/归档完整。

## Notes

- 根协调任务：`/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-12-optimize-user-agents-template/`，权威研究和用户选项记录在根任务 research。它只协调；本组件源码修改由本 task 承载。
- 用户已选：Pennix 全局合同、ALL_TOOLS 一个必要反例、Extra 最小边界、不设硬长度、增加局部范围句。留痕来自既定用户要求。根侧额外测试路径残留由根任务处理，不在组件复制。
- 基线 HEAD `f89b833a490886aa4ecc4e27223ac52ed86105bf`，源模板与本机文件均为 4,476 字节及上述摘要，无非空全局 override；实际实施前再次核对动态事实。
- 只修改 design.md 指定文件；不改运行时、其他组件、安装源合同、Skill 名称/白名单或远端设备。发行沿 Git，无额外 npm/插件发布。
