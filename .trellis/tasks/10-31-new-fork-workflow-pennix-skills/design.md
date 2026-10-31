# 设计：Pennix Skills 主线路由与正式会话交接适配

## 边界

本设计落实父任务步骤 5 和 9，目标基线为 Pennix Skills `088caf16cfd6ff4e20fe08adbb1d503f9d715642`。主线路由 work package 修改 `pennix-workflow-routing`、`pennix-decision-grill` 及其测试和必要 reference；正式会话交接 work package 修改 `pennix-session-handoff` 的 Skill、adapter 脚本和测试。两个 work package 共用一个 owner task，但分别形成独立提交、验收收据和失败处置。步骤 8 只固定已验收的主线提交；步骤 9 完成附加适配后，步骤 10 再固定包含该适配的后续提交，因此附加适配不阻断主线。

## 主线路由 work package

`pennix-workflow-routing` 是跨组件请求的路由说明。它首先确定工作域、交付模式、执行类别、决策前沿和批准模式，再返回负责组件、允许入口、状态写入组件、退出条件及重新规划触发条件。源码维护仓库、安装工具和状态写入组件可以不同，路由输出必须分别写明。

五个阶段的参与关系按职责表达：阶段 1 主要整理目标、范围、需求基线和用户确认；阶段 2 构造决策空间并处理实质取舍；阶段 3 形成方案、核对外部参考、合同和治理；阶段 4 按已批准方案实施、验证、处理阻塞和必要回退；阶段 5 审查交付、验证结果、遗留处置和收尾。实际任务可以跳过不适用阶段或在证据不足时回流，Trellis CLI 才写入阶段转换。

路由对 Trellis Teamwork、Paseo、Lifecycle、CodeGraph、Windsurf Code Search、网页检索、SiYuan、Context Mode、Skills 和宿主接口分别描述调用语义。按需选择工具；不存在交付需求时不自动启用组件。外部官方或流行开源项目的参考在阶段 2、阶段 3 形成正式决策和方案前可用于发现候选、反例、成熟交互和风险，但参考结论必须回到当前任务证据与用户选择，不自动增加阶段、字段、审批或硬性测试套餐。

`pennix-decision-grill` 负责用户拥有的实质取舍：先处理依赖已满足且证据充分的选择，逐步形成决策树，记录选择的影响和适用范围；遇到执行中改变目标、范围、验收、公开接口或权限的决定时停止依赖动作并返回规划入口。它不创建任务、不写 Trellis 状态、不替代 `trellis-idea-to-closed-plan`、不把推荐项当成批准。

## 正式会话交接 package work package

该 adapter 只为用户明确请求的正式跨会话导航服务。源代理先完成任务事实核验和必要准备，再由现有 `pennix-session-handoff` 生成 immutable core、history、prompt 和生命周期收据；目标会话按 `$trellis-start` 重新核验，完整阅读 core 视图和 prompt，历史按需读取。adapter 只协调这些原生入口，不把阶段转换称为 session handoff，也不将任务本身视为 session handoff。

当交接包含任务时，Trellis 原生 ownership 命令仍是任务归属状态的唯一写入入口；handoff receipt 记录其引用和代数，不复制任务指针。`claim`、`consume`、`archive` 仍分开执行并需要目标会话身份及明确继续授权。ready-only 接纳完成后停止，不执行 `pending.next_action`，不关闭 Trellis 任务，不删除资源或运行态。

adapter 与主线路由没有运行时依赖。主线可以在 adapter 未完成时通过主线验收；adapter 失败只影响附加 work package 的验收和最终整体关闭核对。

## 失败、兼容与回退

Trellis 接口未达到稳定合同时，停止步骤 5 和 9 的依赖实施，保留当前方案和证据，回父任务或本 owner task 重新审查。若只是 Skill 文本、链接或测试错误，在当前 work package 内修复并重验。若 adapter 发现 ready、身份、generation 或权限条件不满足，拒绝继续并保留原生收据，不添加绕过路径。所有改动均在 Pennix Skills 独立 worktree 中，未进入根仓安装或发布。
