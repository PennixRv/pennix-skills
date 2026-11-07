## 组件职责

SiYuan 的 `web_search`、`web_fetch` 和 `http_request` 只服务实际知识操作，如用户要求的来源导入。独立网页调研、Codex 官方资料和本地项目定位仍走各自入口，不能借用思源工具作为通用检索或其他检索工具的降级路径。保留思源原生能力，按调用意图选择。

知识、历史回溯和规则晋升按用户意图选择唯一主要来源，见
[`knowledge-promotion.md`](knowledge-promotion.md)。已配置思源的人工知识操作由
`pennix-siyuan-knowledge` 使用原生 MCP；当前 task/源码/spec、`trellis mem` 历史和 formal handoff
各保留自身状态和规定接口。中文技术知识的撰写或改写加载 `$pennix-chinese-tech-writing`，保存仍需具体用户授权。知识失败不阻断任务或交接，禁止无条件预加载、自动捕获与双向同步。

- `Trellis` 是项目 task、任务文件、跨会话状态和工作节点生命周期的权威；context-mode 不决定项目任务语义。正式 handoff 的 `source.rollout.session_id` 只是来源 provenance；目标绑定只能来自当前 Trellis 直接解析的 `source=session:<target-key>`，不能把旧 session 或 `session-fallback:<key>` 当作目标。
- 项目 `AGENTS.md` 与 `.trellis/spec/` 保存项目事实、任务合同和项目特殊路由；Skill 不覆盖更近的项目规则。Trellis 原生模板、骨架与机械惯例优先，自定义中文正文采用写作方法；生成资产仍回实际模板来源修改。
- CodeGraph 配置、使用边界和原生 MCP/CLI 手册索引交 `$pennix-codegraph-integration`；系统部署交 lifecycle，项目操作保留其原生入口与明确授权。
- 确有独立证据价值的工作遵循当前项目选择的 Teamwork 合同；Trellis 维护 assignment、持久报告和协作生命周期，主会话保留项目事实、验收和 Git。
- 核验后的研究事实、候选、不确定性及决定影响写回当前阶段产物、research 或 execution 等已有自然落点；不依赖不存在的研究留存 Skill，不另建事实台账。
- 已初始化项目的 Trellis 资产更新和已选 workflow 刷新由 `$pennix-trellis-project-update` 负责，必须调用当前 Trellis fork 的原生 `trellis update` / `trellis workflow`；系统级组件部署仍由 `$pennix-component-lifecycle` 负责，`$pennix-trellis-asset-check` 只做只读诊断。
- `pennix-session-handoff` 只处理用户明确要求的正式交接；其 immutable core、append-only lifecycle receipt 和确定性 retention 归它所有，但不拥有 Trellis task/pointer。对带 task 的新协议，Skill 只编排 Trellis 原生 `ownership quiesce|seal|retire|claim|consume|archive`，不得自行写 pointer；正式交接通过本地来源封口和配对包验证记录来源收敛。初始 admission 只在 core、prompt、`$trellis-start` 和当前事实完整核对后记录一次 `reconciled`，不完整消费不写 target reservation；后续 `claim` 必须有新的明确继续授权。
- 系统组件部署和 Skills 物化由 `$pennix-component-lifecycle` 编排已登记动作；CodeGraph 项目操作归其原生入口，Hook 实现和配置归事件所属组件及宿主的原生入口。普通路由请求不授权这些高影响动作。
- 工作流资源清理由 `$pennix-resource-cleanup` 负责流程路由；Trellis、Grok、context-mode、服务、容器、系统和远程主机仍分别拥有自己的资源与清理合同。路由 Skill 不执行全局回收，也不替 owner 删除目录。
- Hook/config 和拥有该行为的运行时负责必须发生的事件、阻断、信任、生命周期和审计；提示词只能表达决策原则，不能宣称确定性保证。
