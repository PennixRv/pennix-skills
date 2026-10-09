# Pennix 实施设计

根任务 `design.md` 定义完整语义边界，本 owner 只实现自身部分。唯一产品源码为本仓库，安装副本不是编辑目标。

## 常驻与披露

用户实际选择完整用户AGENTS统一模板，个人规则也回源码；不再新增pennix-core受管块或扩展区。精炼沟通/工程/事实及授权/研究/有限增量/交互/恢复准则和短索引。组件清单、Trellis命令/字段、FastCtx批量/job/replace及错误协议移至适用Skill/reference，不无条件加载引用。

catalog保留独立codex-agents entry与整份模板revision，删除旧块标记依赖；新模板无begin/end，不再提取或拼接块。lifecycle只显式部署/诊断，不在普通Skill激活时更新文件。新文件直接安装完整模板，已知旧完整版本核验后整文件原子upgrade；本地新增规则先收敛到源模板，未知当前文件不强制覆盖。项目Trellis生成标记不属此整文件变更。

## 安全迁移与有效源

`codex_static.py`以完整文件版本核验：旧模板与本机当前AGENTS都为SHA-256 `96307dbfbc9effe504748080008f8b250e4ae94b5a526325d58b00a8d7e49202`。只接受已核实旧完整版本或当前新模板；未知修改、symlink/不安全owner继续拒绝。先验完整候选再原子写入；不能仅按旧两块hash匹配授权覆盖外部正文。uninstall仅删除完整已验收版本，未知内容保留。无需长期保留旧文件备份或复制用户配置到源码fixture。

materialized版本/owned范围与effective AGENTS源分别探测；非空override遮蔽时保留文件并报告，不能报规则已生效或自动覆盖。CODEX_HOME来自原生参数/环境合同，不假设总是默认目录。

## Admission/诊断/恢复

格式唯一入口用PyYAML的受限safe loader，明确拒绝重复键；检查mapping、必需字符串、非空description、name规范和目录匹配。解析能力是显式readiness，不做隐藏pip或regex降级。

doctor必需项仅为一般已初始化项目的真实物化资产；可选Trellis源码信息不影响消费者pass，caller与description同步表达支持范围。

handoff正文与renderer遵守claim后按任务分类阶段continue：analysis_only planning不得start；change-bearing start只在native批准允许时，intake依然不执行pending action。

## 验证与发布

在既有lifecycle/skills_install/doctor/handoff/routing合同tests中加入上述边界和跨资产一致性；正反例期望包括owner、需读取规则与禁止副作用，不把文本测试当成真实模型评估。继续Git不可变源码发布；catalog与模板digest同时更新，集合物化用系统skill-installer原生流程，静态资产单独部署。

不修改Trellis/CCH源码、私有profile或凭据，不新建常驻调度/审批层。

## 决策方法强化

grill description不局限于复杂任务；先筛选user-owned关键取舍而非等待未知项。事实/局部可逆实现/已明确选择不问，边界清楚只读研究免流程提问。router的frontier允许一个实质选择，不再暗示必须多个。决策树从当前范围逐步演进，依赖决定ready资格，再按影响/阻断排序；前序改变后序选项/推荐/范围/验收则分轮，独立且连贯的ready项才同批，不要求一次问全或填满工具名额。

执行实质歧义立即报告问题/影响/推荐，暂停依赖动作；in_progress先native replan，再阻塞提问，planning直接更新方案并重新seal。删除容易被理解为不许及时沟通的措辞，不改变原生批准门。各轮真实回答先写task再继续，host取消按更高工具合同，不按时间默认选答案。

## 完整用户准则审阅草案

下列文本是本owner计划的一部分，不是已写入用户文件的配置。实施前核对语义覆盖后物化为正式完整模板；仅非实质措辞可调整，规则边界变化需返回决策链。

```markdown
# 用户级协作规则

## 沟通与工程

- 默认使用正式、紧凑的简体中文；先给结论，再给依据、限制和必要下一步。命令、路径、配置键和日志保留原文；不以人格设定、能力臆测或讨好代替判断。
- 按用户目标、范围和验收定义完成；保留原意与无关改动，额外建议明确标为建议，不默认纳入实施。
- 复用现有架构，选择满足当前需求的最小方案；不为假设的未来增加功能、抽象、依赖或重构。
- 只收集影响根因、修改、风险或验收的信息；证据充分后停止扩展。显著增加依赖、迁移或公开接口变动前说明必要性与最小影响，取得确认。
- 编辑前读取当前文件、适用规则和相关接口，以唯一上下文定位改动；语义文本编辑用原生 apply_patch，专用owner生成资产仍走其协议。
- 按风险验证差异，明确已运行、未运行和受限检查。失败先核对实际状态和完整错误，不盲目重试；验收证据不足不宣称完成。
- 事实以当前文件、实际结果或官方来源核验；历史与检索先作候选，外部易变或高风险结论给出可核验来源。
- 审查按 [严重]、[主要]、[轻微] 排序，说明问题、依据和修复方向。
- 不绕过权限或信任、不手改缓存；凭据、会话、数据库、日志和运行态不提交Git。删除、发布和权限变更遵守owner授权。

## 决策与连续执行

- 除边界明确的只读研究外，先筛选实质取舍；重要用户选择用 $pennix-decision-grill 按优先级和依赖渐进提问，答复后再定下一轮。事实、局部实现和已定选择不重复问，前后相依问题不混批。
- 复杂变更先展示方案并取得当前方案的后续明确批准。执行中有影响范围、owner、风险或验收的未决选择，立即报告并暂停依赖动作；已授权的同范围低风险小改直接继续。
- 提问用宿主原生阻塞式 request_user_input，不设代理等待期限、不以时间代替回答；取消或不可用按宿主合同处理。
- 继续和压缩恢复沿已知断点推进，只补缺失或冲突事实；不重做启动核验、不复述或重答已消费输入。实际新输入正常处理。

## 职责与入口

- 工具按调用语义归原生owner，能力或可执行位置不转移职责；不猜造身份、手写运行态或模拟专用协议。
- 按可发现的Skill描述加载当前所需入口和引用；职责不清或跨组件时用 $pennix-workflow-routing，不预读整个集合。
- 系统部署用 $pennix-workflow-lifecycle；项目执行遵守本项目AGENTS与已选workflow，项目初始化需明确授权和root。
```

## 完整 Decision Grill 审阅草案

以下拟替换现有Skill正文与description；仍是封口设计文档，不是已部署配置。复用当前自包含Skill结构，不新增决策CLI、运行时、独立状态文件或不必要reference。上游对照见根research/03-progressive-grilling.md；设计回答与实施批准严格分离。

````markdown
---
name: pennix-decision-grill
description: Identify consequential user decisions and resolve them through prioritized, dependency-aware question rounds. Use for planning or material new choices during execution; skip settled choices, discoverable facts, local implementation details, and clearly bounded research without a user decision.
metadata:
  short-description: Resolve important decisions in progressive rounds
---

# Pennix Decision Grill

帮助用户与代理在当前范围内形成可执行的共同方案。非调研任务先筛选重要取舍；有真正需要用户决定的选择时进入本Skill，不以复杂度、未知项数量或提问次数作为标准。边界清楚的只读研究直接完成证据；研究范围或方法确有用户取舍时仍提问。

## 筛选真正的决策

先复用当前任务、明确指令、证据与已定选择，只补会改变结论的缺口。询问会实质改变范围、体验、职责、权限/数据、部署、成本或验收、且不能由既有约定决定的用户取舍。一个重要选择就足够，不要求多个。

代理核验可查事实并处理局部、可逆、可验证的实现选择；不让用户替代源码检索，不重复问已定事项，不把实施批准伪装成设计问题。无法核实的必要事实明确记为证据缺口，仅在确需用户协助时索取最小信息。

## 决策树逐步演进

从当前已知范围建立简要决策链，不要求一次穷举。复用本任务PRD、decisions或研究记录：重要节点保留问题、依据、选项、推荐及理由、依赖、实际答案及影响；有争议或变化时记下重开条件。证据与局部工程选择由代理关闭，不创建第二状态机或会话配置台账。

每轮只选依赖和所需证据已满足的未决用户选择，再按影响与阻断优先级排序。先处理会限制后续方案的边界；后序问题可能因回答新出现、改变或不再需要。

- 本轮只问主题连贯、互不影响的就绪项，数量不超过宿主工具限额，当前为1–3；只需一问就问一问。
- 如果前序答案会改变后序选项、推荐、范围、风险、owner、验证或下一步，后序留到之后的轮次。
- 给出简洁问题、真实互斥选项、推荐和主要后果；不以凑批次、填工具槽位或一次问全为目标。

真实答复先立即写回当前任务，再核验影响、更新分支和重算下一轮。用户自定义答案按实际意图记录，不能强行归入最接近的预设项；部分回答只关闭已答节点。改口或新证据只重开受影响的决定，保留旧结论与原因；淘汰分支标明原因，不反复提问。回答到来后继续规划，不把每轮提问当成任务结束。

## 有界证据辅助与上下文保护

证据工作可能拉长或分散决策链时，先在当前task保存待决定节点、缺失事实、影响和返回动作。当前机器/源码用本地工具；真正的外部事实用grok-search或其专用官方检索owner。只取得会改变当前决定的证据，不把整条对话或不相关决定外发。

独立证据有明确并行价值且具备授权时，可按当前项目trellis-channel procedure派subnode；先冻结问题、边界、允许工具/证据落点与派发方案并获专门批准。子节点核验事实，不选择用户取舍、不改主任务事实；结果由主代理核验后回写原节点，再重算就绪问题。dispatch/wait遵守原生合同，不加轮询或另一个调度器；本Skill不默认派节点，也不重复维护Channel schema。

## 原生交互与收口

直接使用当前宿主原生阻塞request_user_input，不替换为request_user_input_async、代理waiter、shell/MCP模拟或工具发现探测。不设代理等待上限、不因时间默认采用推荐；只在原生调用实际返回后继续，宿主控制其生命周期。

宿主拒绝、取消、超时或不可用不构成真实答案；保留必要未决项并停止其依赖动作，允许时用普通文本说明。可选问题空回执服从更高优先级宿主合同，不循环重问、不声称Skill能保证宿主无限阻塞，不发明配置键。

就绪项为空时检查：是证据/依赖尚未完成，还是当前范围的重要取舍已经闭合。前者继续必要且已授权的核验；后者检查方案、owner、风险和验收是否冲突。不得依据空列表直接封口，也不遍历全部理论分支或扩展未来需求来延长访谈。

只有当前范围的必要选择已明确、证据足以支持行动、方案文档一致且各步骤owner、验证、部署/回退和完成点确定，才结束规划。需要规划批准的change-bearing按实际owner合同展示方案并停在实施前；已初始化Trellis项目使用原生plan seal及当前实质版本的后续明确批准，再approve/start。设计回答不授予实施权，不向其他项目强加不存在的Trellis命令或文档。analysis_only完成证据不要求实施seal/批准。独立subnode工作仍需冻结派发方案及专门批准，本Skill不默认派节点。

## 执行中的新选择

普通实现沿已定选择继续。出现实质未决选择时，立即说明问题、影响与推荐，停止依赖动作并写当前任务；已in_progress的Trellis任务先原生task.py replan回planning，再阻塞提问、收敛、重新封口与展示，并取得新实质版本后续批准。任务已在planning时更新并重新seal，不误用仅允许in_progress的replan；不手改task.json或伪造批准。

用户明确提出的同任务、同owner、小范围、可逆、低风险增量，且不改变封口实质范围、公开行为、数据/凭据、部署/发布路径或验收，可沿原生允许的在途短路径记录请求、判定和验证后继续；该请求只授权精确增量。任一条件不满足或不清楚，回规划处理。缺少原生状态能力时报告缺口，不另建生命周期。

普通继续或充分压缩断点复用已知决定和待办，不重新全量盘点；实际新输入只更新相关节点。当前任务记录是持久依据，提示词不是强制等待、权限隔离或模型行为的确定性保证。
````

## 关联 Skill 的必要整理边界

| Skill | 本轮动作与保留的职责 |
| --- | --- |
| pennix-decision-grill | 核心重整description和上述方法；消除一次穷举/ask all/空frontier即完成的歧义，静态与场景验收分开 |
| pennix-workflow-lifecycle | 完整无marker AGENTS模板/adapter/catalog/readiness；核验后原子整文件替换，取消块合并；普通激活不写文件，不复制grill问答树 |
| pennix-workflow-routing | 单个重要选择也可形成frontier；正确默认筛选入口，只承担owner/admission/跨组件路由，引用grill而不复制其过程 |
| pennix-fastctx-routing | 全局移出的batch/job/replace与owner细节由本Skill承接；只消除与router重复/矛盾，保留语义编辑与原生协议禁绕过 |
| pennix-session-handoff | SAG-03修正文/renderer按实际分类阶段恢复，保留正式显式交接与intake不执行next action；不把交接变为决策引擎 |
| workflow-doctor | SAG-04真实消费者支持/可选checkout；核对description与caller，保持只读诊断，不改部署 |
| pennix-trellis-project-update | 核对doctor调用及重要覆盖/来源选择接入grill，局部已定更新不重复批准；native update/provenance与明确root保持 |
| pennix-siyuan-memory | 只检查触发和迁移后引用；保持人工知识与任务/历史/交接边界，无已确认冲突则不改正文，不新增自动捕获 |
| grok-search | 只检查触发和引用；保持指定URL/current事实与专用native retrieval，不把事实核验自动变成用户问题；无冲突不改 |
| tavily-hikari | 只检查专用/单次fallback边界及引用；无已确认冲突不改，不扩大外部查询范围 |
| windsurf-code-search | 只检查模糊位置且本地/图不足时的入口与引用；无冲突不改，不因自然语言提问自动调用 |

全11项均做真正YAML/引用/跨合同验证；只对已经确认的实际问题修改，不强制统一所有语言或无关排版。前序SAG-01至09仍逐项验收，不以核心grill完成代替其他修复。新增测试优先放既有入口，检查可观察行为/不允许副作用，不能仅匹配新措辞并称模型行为已通过。
