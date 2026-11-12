---
name: pennix-project-agents-governance
description: 审查、规划或维护项目级 AGENTS.md 的内容、有效来源链和原生生成块，并编排明确授权的项目初始化、重初始化、刷新和移除；用于相关规则或模板变更、冲突及未知 writer，不用于每次开发任务、系统部署或未经授权的自动初始化。
---

# 项目 AGENTS 治理

治理对象是项目指令文件；手工正文与 Trellis、CodeGraph 等生成块都在文件内部。默认只读；明确授权的项目操作由主 Agent 按下文串行编排原生 owner。Codex 主会话和 Trellis 独立 Codex 节点是功能保障范围，其他宿主仅给已核验兼容说明。触发来自相关规则、writer、模板或宿主配置变更，或明确的项目接入、重入和退出请求，不给每个新会话或 Trellis 开发任务增加检查。涉及项目操作时，必读[项目操作编排合同](references/project-operations.md)；本 Skill 不新增脚本、CLI、执行器、组件 registry 或持久执行台账。

## inspect：确认实际来源和 owner

先明确真实项目根、checkout/submodule 边界、cwd、宿主、已选组件和精确动作、可见用户规则、适用目录规则和当前任务。按[来源链说明](references/codex-chain.md)识别用户层及 root→cwd 的逐层 override/fallback；inspector 的 `host_loaded=false` 始终只是静态候选，不等于宿主已加载。备份、样例和独立仓库不混入活动链。

逐个文件标出内部手工区域、生成块、来源模板、原生 writer、实际写入路径及 install/update/refresh/uninstall 调用方。按项目操作合同的有界证据分类直接 writer、全局／用户层 writer、消费者及可选／未知项。Trellis 拥有 TRELLIS 块，CodeGraph 拥有 CODEGRAPH 块，Lifecycle 的 codex-agents 拥有用户层模板。未知 writer 先找初始化器、脚本、Hook 和 package lifecycle 的真实调用证据；不接管其写入，也不声称已发现任意第三方 writer。GitNexus 是项目特定案例，不默认成为 Pennix 组件。

## plan：确定内容与冲突

项目手工正文保存项目特有约束、仓库/目录边界、基本构建验证入口及必要导航；详细任务流程归 workflow，编码合同归 spec，按需方法归 Skill，MCP 协议归原生 instructions/help。必要受众摘要可以共存，语义相似本身不是冲突。

比较实际适用的手工正文、生成内容和可见用户规则。按安全风险、硬冲突、条件张力、普通重复/过时导航报告证据、适用条件和修复 owner。系统/开发者规则不可见时记录审计限制，不声称检查完所有层级。合法项目特有要求可以细化用户规则；不从治理策略推导新的宿主优先级。

未知 owner、异常/重复 marker、符号链接或路径风险、可能覆盖手工正文、安全风险和明确硬冲突阻断受影响操作；一般重复和条件张力报告后可继续无关范围。生成模板发布或规则变更前完成语义兼容审查；原生 writer 仍单独保证确定性写入安全，不绑定用户规则版本/hash。

项目操作计划复用当前任务和已有授权，列明每个已选 owner 的原生命令、顺序、预期文件与块、后置条件、冲突处置及失败重入点。未选组件保持，不因工具缺失自动部署，不因项目接入自动授权索引。AGENTS 外的共享配置和其他生成资产须单独核对原生覆盖范围；不能用整次 `init --force` 绕过单个缺块。已有充分授权不重复询问，实质变化仅停止依赖动作并交回主 Agent。

Trellis 接入还须区分入口准备与项目规范建立：盘点 `.trellis/spec/index.md`、实际 package 导航、旧占位及真实条目，明确本次是否包含建立／刷新规范。包含时衔接宿主实际声明的 `trellis-spec-bootstrap`，复用当前任务与授权；未声明则报告限制，不猜路径或自动安装。普通资产更新不隐含语义迁移。

## apply / delegate：沿授权和原生入口修改

按当前明确请求展示手工正文候选差异，再用原生 apply_patch 做最小修改。生成块先列出目标和预期差异，委托原生 owner；不手改生成块或摘要。Trellis 项目资产更新用 `$pennix-trellis-project-update`，CodeGraph 项目集成用 `$pennix-codegraph-integration`，系统安装/升级用 `$pennix-component-lifecycle`。仅审查文件不授权初始化、索引、安装、发布或卸载。

项目初始化、重初始化、刷新和移除按项目操作合同逐步执行，每步回读后才进入依赖动作。失败保留已成功结果和现场，区分已完成、部分完成、未核验及未选动作，从失败 owner 最小原生重入；不自动卸载其他已成功 owner，不手改 manifest/hash 消除冲突。

## verify：回读与留痕

核验来源模板、实际物化文件、唯一 marker、块外正文、override/fallback 和截断限制；项目操作还要联合核验全部已选块、项目配置及未选组件，并在隔离 fixture 验证 Trellis→CodeGraph 与 CodeGraph→Trellis 两种顺序、重复执行和失败重入。真实用户文件不作破坏性测试。区分源码、发布、安装、物化、来源候选、宿主信任、实际加载和 MCP 生效；退出码 0、单个目录或版本文件不足以证明整体完成。结果写当前 task/Issue，长期可执行合同只写相应 spec；不创建全局 registry、重复台账或常驻扫描器。

返回结论应包含受影响文件及内部区域、owner、确定问题与受限项、已执行/未执行的检查和下一落点；验收不足保留未完成状态。

报告 spec 时分别说明入口处理、真实规则的源码依据、活动导航、占位／历史处置和未完成项。文件存在、旧字节保持或 init 成功不能证明规范有效；仅准备入口的请求应明确内容尚未验证，不扩大为完整规范治理已完成。
