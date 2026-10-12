# Pennix 集成设计

## 来源与授权

执行根任务 `matt-skills-pennix-lifecycle-plan` revision 3 中明确列出的 Pennix 修改面。用户已在展示该完整封口包后明确批准修复、提交推送、必要发布、重装、落点更新与收敛。本组件记录是该方案的执行投影，不把新选择或未展示方案冒充既有批准。

## 修改目标与边界

源码为本仓库；分支 `task/matt-skills-extra`，目标 `main`。安装树只是交付副本。先核对获批的 FastCtx `codex-native-nesting` 任务，串行处理共享 Pennix 路由文件；不在此改 FastCtx 源码或固定输出池。

P0 修改 lifecycle 的 `templates/AGENTS.md.install`、workflow routing、FastCtx routing、decision grill 及已有契约测试；更新模板分发摘要并按受管证明/漂移合同安装。`ALL_TOOLS` 只描述其编排器调用面；宿主工具存在性由宿主实际声明和真实调用判断。交互按宿主合同，不通过 MCP 清单探测。Guarded 容量、外层截断、schema、权限、传输、服务和命令失败分别保留。

Grill 在当前任务自然落点记录原始目标、成功信号、重要决策/依赖、要求与验收关系。分类区分待证据、依赖阻塞、不能精确表述、已决定、延期和排除；回答和证据到来后重算就绪前沿。Trellis 负责整体规划和原生封口；Grill 不接管生命周期。术语解释会影响取舍时用少量具体情境核对，不强制 Glossary/ADR。

中文技术写作只更新 `references/workflow-assets.md`：平衡常驻上下文成本与条件引用的漏读/查找成本；同概念的规则与例外共置，外置仍保留触发条件和唯一真源。

第二集合复用 `scripts/adapters/skills_install.py` 的精确树校验、staging 和事务替换；泛化现有 resolver、目标/receipt 与 per-action owner 分派，不新建安装框架。新 ID 为 `pennix-skills-extra`，固定公开 fork 和审核 SHA；路径与名称来自唯一 catalog 白名单，安装者不能覆盖。无 bootstrap、安装后命令、MCP/Hook 或任意执行器。

十项为 `diagnosing-bugs`、`codebase-design`、`prototype`、`improve-codebase-architecture`、`retro`、`teach`、`loop-me`、`writing-fragments`、`writing-shape`、`wait-what`；原始路径由根设计和 fork 树核验后固定。

从宿主受信 `.system/skill-installer` helper 定位已有安装器，使用 argv 数组与 download 模式，仅物化到本次受管 staging；缺失/不可信拒绝。新集合有独立目标和 receipt，记录 repo、SHA、精确集合及 digest。完整旧 SHA 可升级；同 SHA 幂等；未知来源和漂移拒绝。树与 receipt 一起提交或恢复旧版；清理仅涉及本次 staging。旧 Pennix bootstrap、命令链接、配置和 receipt 合同不迁移。

## 交付和回退

精选 fork 先提交推送并公开可读，再 pin catalog、回归、提交推送 Pennix。旧集合由系统 installer staging 和 lifecycle `replace-staged` 接纳，新集合由 managed install 接纳。隔离验证先于本机；不覆盖用户 AGENTS 修改或手改 receipt/hash。精选回退通过 catalog 恢复审核旧 SHA，再原生 upgrade/verify；首次安装可精确卸载。实际宿主发现/触发受限须如实 blocked。

精确合同见根任务 revision 3 的 `design.md`、`research/04-lifecycle-second-collection-contract.md`、`research/15-idea-decision-map-grill-plan.md` 和 `research/17-host-tool-availability-surface.md`。改变 membership、owner、来源执行、部署/发布、公开行为或验收须回规划；动态版本和权限在既定合同内核验。
