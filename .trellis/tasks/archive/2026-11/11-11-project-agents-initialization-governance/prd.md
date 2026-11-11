# 项目 AGENTS 初始化治理与路由实现

## 目标（Goal）

承接根任务 trellis-project-governance-spec-orchestration 已批准合同 W2：现有治理 Skill 和路由的原生项目初始化编排、部分失败恢复与联合验收方法。根任务统一实施与发布部署授权，不新增执行器或独立方案。

## 需求（Requirements）

- 本记录承接单一根任务 `trellis-project-governance-spec-orchestration` 的已批准 W2，不是新方案或独立批准流程。
- 根合同与真实批准位于组件根目录相对路径 `../.trellis/tasks/in_progress/11-11-trellis-project-governance-spec-orchestration/`；按 N1 Agent 编排路线实施。
- 完善现有项目 AGENTS 治理 Skill、路由和必要引用，明确原生 owner、项目根、选定动作、失败恢复与联合核验；不新增执行器、命令、registry 或状态机。
- 根 owner 控制阶段、集成、Git 提交和发布部署；实施者只修改本组件源码/测试/文档，不递归委派、不向用户提问、不使用 Copilot。

## 验收标准（Acceptance Criteria）

- [x] 方法覆盖初始化、重入、更新、撤回与部分失败，保留系统部署及原生 project-update 边界。
- [x] 原生作用域、refresh 限制、来源与加载、未知 writer 和并发限制准确。
- [x] 目标测试与集合验证通过，源码实施者未触碰用户安装副本、秘密和运行态；正式物化由根侧沿原生 Lifecycle 完成。

## 备注（Notes）

- 同一根任务已完成决策和整体授权；本组件只维护源码 owner 的执行证据，不另建方案或重复询问。

## W2 执行摘要（2026-11-11）

- 已扩展治理 Skill 的触发及 inspect → plan → native apply/delegate → verify，新增按需引用 `references/project-operations.md`，覆盖有界 writer 分类、项目根与选定动作、双向顺序、N2 目标行为、部分失败重入、撤回／恢复、摘要与并发限制及联合核验。
- 已同步 workflow-routing 主入口、场景与组件归属引用，并在 Trellis project-update 和 CodeGraph native-manual 澄清原生职责及受限 local install。inspector 实现、`host_loaded=false`、`collection.json` 权威和既有命令均保持。
- 验证通过：治理／inspector 5 项、workflow-routing 6 项、project-update 3 项、根 tests 15 项；`python3 scripts/collection.py verify` 验证 19 Skills、2 commands；7 份变更中文文档的只读文案检查通过。新增测试只验证方法引用与 owner 导航完整性，不将段落存在当作 writer 行为证据。
- Context Mode 的 resume 和执行器调用均返回 `Invalid argument Codex threadId/session_meta`；读取按宿主允许的原生有界分页回退，未修复或改写会话环境。首次大文件原生读取被输出大小 Hook 阻断，后续完整分页取得；不属于访问权限拒绝。
- W2 仅交付本组件方法、引用和测试；未调用项目 writer、建立／重建索引、修改安装副本、执行 Git／任务阶段／发布部署操作。W1 的 N2 writer 实现、W3 的真实跨 writer 组合与宿主加载验收由根 owner 集成，本地静态检查不能替代这些结果。新增治理合同归 Skill 的稳定引用，无须在组件 spec 重复维护同一合同。

## 根侧复核与交付

主会话复核实际源码，重新执行上述 29 项测试及 collection verify，均通过；独立 reviewer 未报告本组件的具体缺陷。源码提交 `9563702a9b71c6f27c98f65d4a94847275938057` 已推送，集合原生 CI `42984440071` 成功。Lifecycle `v0.2.53` 固定该提交并经原生工具完成集合物化；选定治理与路由文件和源码一致，config check 通过、recover 为 idle，配置指纹保持。

本记录仅为根任务 W2 的组件 bookkeeping，未单独发起实施路线；使用既有 archive 原生入口及明确原因关闭，不倒填本组件过去的方案或授权状态。根任务保留 Trellis 产品实现、组合验收和整体接受职责，当前记录关闭不表示其整体已经完成。
