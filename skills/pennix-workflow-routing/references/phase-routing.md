## 各业务阶段中的组件路由

目标 Trellis fork 的 bundled workflow 和各自独立的阶段 Skill 决定阶段内工作顺序与转换。下表只说明跨组件路由；组件按当前需要参与，不是每个阶段的必备清单，未选能力不列为该路线前置条件。阶段状态、路线、授权和接受结果由 Trellis CLI 写入。

| 阶段 | 路由重点 | 可能参与的组件与边界 |
| --- | --- | --- |
| 目标探索与需求核对阶段 | 建立目标、范围、验收目标和约束的当前基线，并取得用户确认 | `trellis-goal-exploration-and-requirements` 负责本阶段工作；按问题选择本地代码、外部资料或用户维护知识来源。`pennix-decision-grill` 只处理会改变目标基线的重要用户取舍。 |
| 决策空间构造与归并阶段 | 构造与筛选实质候选；只有选项依赖或条件分支会改变后续决策时才展开决策树 | `trellis-decision-space-construction-and-merging` 负责决策空间；按需参考外部先例，普通外部检索优先 Tavily；`trellis-teamwork` 可提供只读证据。用户保留决定整理给第三阶段，再由其按需委托 Grill。 |
| 解决方案设计与收敛阶段 | 解决保留的用户决定，形成并核对完整方案及适用的实施合同 | `trellis-solution-design-and-convergence` 负责收敛；触发 prior-art review 时，在接受正式方案前核验相关开源实现或公开提案。当前宿主声明的 `codebase-design` 可辅助实际涉及的模块接口或边界设计；`prototype` 仅在具体模型不确定性适合交互验证时考虑。两者都不是目标 Trellis fork 的 bundled 依赖或阶段门禁。`pennix-decision-grill` 负责必要的同步用户取舍；Trellis CLI 接受阶段结果。 |
| 任务实施与测试验证阶段 | 按已接受且获授权的合同实施、集成和验证 | `trellis-task-implementation`、源码 owner 仓库规范、`trellis-before-dev` 与 `trellis-check` 负责相关工作。CodeGraph、Context Mode 或语义代码搜索按问题选择；当前宿主声明的 `codebase-design` 仅在确有模块接口或边界设计问题时提供方法，`diagnosing-bugs` 仅在难定位缺陷或性能回退需要系统诊断时参与；修复后的复发预防由 `trellis-break-loop` 按需处理。`trellis-teamwork` 只提供只读协作；只有明确授权写入型委派时才由 Paseo 管理 Git worktree。组件部署和项目资产更新仍分别交 Lifecycle 与 Trellis 原生入口。 |
| 交付审查与现场收尾阶段 | 核对当前交付及合同内必需工作，处置缺口或允许保留的遗留 | `trellis-delivery-review-and-closeout` 与 `trellis-check` 按实际风险审查；只有存在必要用户决定或合同要求用户接受时，才由 `pennix-decision-grill` 协助同步交互。必要时调用资源 owner 的清理入口。`trellis-finish-work` 只负责会话收尾，不代替 Trellis CLI 对阶段结果的核验和接受或任务完成操作。 |

`pennix-session-handoff` 仅在用户明确要求时作为独立附加操作执行，不是阶段转换、实施或任务完成的前置条件，也不改变以上路由。

上述扩展 Skill 只在当前宿主已声明且具体触发条件满足时作为辅助方法；它们不是目标 Trellis fork 的 bundled 依赖，也不拥有阶段状态、方案接受或用户授权。
