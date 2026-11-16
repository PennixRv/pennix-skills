# 设计：Pennix Skills 审查、主线路由与正式会话交接适配

## 边界

本设计落实父任务步骤 5 和 9。既有主线路由和正式会话交接适配分别从 `aabe97d` 与 `967d18c` 延续，并已包含在当前 `main` 历史中；本轮扩展对正式集合全部 16 项 Skill 的适用性审查，并按证据修复工作流相关内容。主线路由 work package 可修改正式集合中经审查确认有问题的 Skill、必要 reference 和相关测试；正式会话交接 work package 仍只修改 `pennix-session-handoff` 的 Skill、adapter 脚本和测试。

所有源码继续在根仓 `pennix-skills` submodule 的既有 `main` checkout 中修改；不另建分支或 Git worktree，也不改写 `aabe97d`、`967d18c` 及其后的提交。主线路由与会话交接适配以逻辑工作包分别审查和记录验收收据，工作区差异和提交按现有主线顺序保留。主线路由收据用于父任务主线验收；会话交接收据仍是优先级较低的独立附加交付，不进入主线路由或主线准入，父任务整体关闭前单独核对。当前 `main` 已含这两类工作的既有提交历史，因此不得为恢复旧的纯主线分叉而 reset、cherry-pick 重建或删除有效提交。

## 主线路由 work package

本 work package 先复用父任务的 `research/pennix-skill-phase-participation-audit.md`，逐项审查 `collection.json` 中的 16 项正式 Skill。审查其触发描述、职责、阶段参与关系、与其他 Skill 的边界和有效链接；仅在相关 reference、元数据或测试有助于核实具体问题时再读取。每项审查结论回写到父任务已有阶段参与记录或本 owner task 执行收据，不另建重复的全量目录。只有直接参与本工作流且发现可核验缺陷的资产才修改；不相关或正确的 Skill 保留原文。根仓 `pennix-skills-extra` 是独立 submodule，由父任务只读审查，本 owner task 不写入。

`pennix-workflow-routing` 是跨组件请求的路由说明。它首先确定工作域、交付模式、执行类别、决策前沿和批准模式，再返回负责组件、允许入口、状态写入组件、退出条件及重新规划触发条件。源码维护仓库、安装工具和状态写入组件可以不同，路由输出必须分别写明。

各业务阶段的参与关系按职责表达：目标探索与需求核对整理目标、范围、需求基线和用户确认；决策空间构造与归并整理决策空间并处理实质取舍；解决方案设计与收敛形成方案、核对外部参考、合同和治理；任务实施按已批准方案实施、验证、处理阻塞和必要回退；交付审查与收尾审查交付、验证结果、遗留处置和收尾。实际任务可以跳过不适用阶段或在证据不足时回流，Trellis CLI 才写入阶段转换。

路由对 Trellis Teamwork、Paseo、Lifecycle、CodeGraph、Windsurf Code Search、网页检索、SiYuan、Context Mode、Skills 和宿主接口分别描述调用语义。按需选择工具；不存在交付需求时不自动启用组件。当前任务需要外部检索时优先使用 Tavily；仅在具体操作适合 Grok 或用户/当前路线明确选择 Grok 时调用 Grok。遵守所选 Skill 的失败合同和用户指定来源，不因失败自动轮换服务商。外部官方或流行开源项目的参考可在“决策空间构造与归并”和“解决方案设计与收敛”形成正式决策和方案前用于发现候选、反例、成熟交互和风险，但参考结论必须回到当前任务证据与用户选择，不自动增加阶段、字段、审批或硬性测试套餐。

`pennix-decision-grill` 负责用户拥有的实质取舍：按依赖和证据逐步处理选择；存在条件分支时帮助构造决策树，简单选择可用清单或比较表，不强制套用决策树。它记录选择的影响和适用范围；遇到执行中改变目标、范围、验收、公开接口或权限的决定时，暂停受影响动作并返回规划入口。它不创建任务、不写 Trellis 状态、不替代 `trellis-idea-to-closed-plan`，也不把推荐项当成批准。

审查参考 Anthropic 与 OpenAI 官方 Skill 撰写指南，以及 `pennix-chinese-tech-writing` 对工作流资产和术语的规范。保持渐进披露和清晰触发；指令强度匹配具体权限、副作用和错误后果。官方示例不转成统一长度、固定章节、固定 reference 数量、每阶段强制 Skill 清单或额外路由机制。新增及实质改写的工作流正文使用简体中文，沿用父任务已决术语；平台字段和正式产品标识保持原文。

## 正式会话交接 package work package

该 adapter 只为用户明确请求的正式跨会话导航服务。源代理先完成任务事实核验和必要准备，再由现有 `pennix-session-handoff` 生成 immutable core、history、prompt 和生命周期收据；目标会话按 `$trellis-start` 重新核验，完整阅读 core 视图和 prompt，历史按需读取。adapter 只协调这些原生入口，不把阶段转换称为 session handoff，也不将任务本身视为 session handoff。

当交接包含任务时，Trellis 原生 ownership 命令仍是任务归属状态的唯一写入入口；handoff receipt 记录其引用和代数，不复制任务指针。`claim`、`consume`、`archive` 仍分开执行并需要目标会话身份及明确继续授权。ready-only 接纳完成后停止，不执行 `pending.next_action`，不关闭 Trellis 任务，不删除资源或运行态。

adapter 与主线路由没有运行时依赖。主线可以在 adapter 未完成时通过主线验收；adapter 失败只影响附加 work package 的验收和最终整体关闭核对。

## 失败、兼容与回退

Trellis 接口未达到稳定合同时，停止步骤 5 和 9 的依赖实施，保留当前方案和证据，回父任务或本 owner task 重新审查。若只是 Skill 文本、链接或测试错误，在当前 work package 内修复并重验。若 adapter 发现 ready、身份、generation 或权限条件不满足，拒绝继续并保留原生收据，不添加绕过路径。所有改动均在根仓 `pennix-skills` submodule 的既有 `main` checkout 中；完成父任务集成验收前不更新根仓 gitlink，不执行发布或安装。
