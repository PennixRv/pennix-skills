---
name: pennix-project-agents-governance
description: 审查、规划或维护项目级 AGENTS.md 的内容、有效来源链和原生生成块；用于相关规则或模板变更、冲突及未知 writer，不用于每次开发任务、系统安装或自动项目初始化。
---

# 项目 AGENTS 治理

治理对象是项目指令文件；手工正文与 Trellis、CodeGraph 等生成块都在文件内部。默认只读。Codex 主会话和 Trellis 独立 Codex 节点是功能保障范围，其他宿主仅给已核验兼容说明。触发来自相关规则、writer、模板或宿主配置变更，不给每个新会话或 Trellis 开发任务增加检查。

## inspect：确认实际来源和 owner

先明确项目根、cwd、宿主、可见用户规则、适用目录规则和当前任务。按[来源链说明](references/codex-chain.md)识别用户层及 root→cwd 的逐层 override/fallback；静态候选不等于宿主已加载。备份、样例和独立仓库不混入活动链。

逐个文件标出内部手工区域、生成块、来源模板、原生 writer、实际写入路径及 install/update/refresh/uninstall 调用方。已知 owner：Trellis 拥有 TRELLIS 块，CodeGraph 拥有 CODEGRAPH 块，lifecycle 拥有完整用户模板。未知 writer 先找初始化器、脚本、Hook 和 package lifecycle 的真实调用证据；给出通用组件或项目特定集成的归类建议，不接管其写入。GitNexus 是项目特定案例，不默认成为 Pennix 组件。

## plan：确定内容与冲突

项目手工正文保存项目特有约束、仓库/目录边界、基本构建验证入口及必要导航；详细任务流程归 workflow，编码合同归 spec，按需方法归 Skill，MCP 协议归原生 instructions/help。必要受众摘要可以共存，语义相似本身不是冲突。

比较实际适用的手工正文、生成内容和可见用户规则。按安全风险、硬冲突、条件张力、普通重复/过时导航报告证据、适用条件和修复 owner。系统/开发者规则不可见时记录审计限制，不声称检查完所有层级。合法项目特有要求可以细化用户规则；不从治理策略推导新的宿主优先级。

未知 owner、异常/重复 marker、符号链接或路径风险、可能覆盖手工正文、安全风险和明确硬冲突阻断受影响操作；一般重复和条件张力报告后可继续无关范围。生成模板发布或规则变更前完成语义兼容审查；原生 writer 仍单独保证确定性写入安全，不绑定用户规则版本/hash。

## apply / delegate：沿授权和原生入口修改

按当前明确请求展示手工正文候选差异，再用原生 apply_patch 做最小修改。生成块先列出目标和预期差异，委托原生 owner；不手改生成块或摘要。Trellis 项目资产更新用 `$pennix-trellis-project-update`，CodeGraph 项目集成用 `$pennix-codegraph-integration`，系统安装/升级用 `$pennix-component-lifecycle`。仅审查文件不授权初始化、索引、安装、发布或卸载。

## verify：回读与留痕

核验来源模板、实际物化文件、唯一 marker、块外正文、override/fallback 和截断限制；按改动风险使用 owner 的隔离 fixture，真实用户文件不作破坏性测试。区分源码、发布、安装、物化与宿主加载五层。结果写当前 task/Issue，长期可执行合同只写相应 spec；不创建全局 registry、重复台账或常驻扫描器。

返回结论应包含受影响文件及内部区域、owner、确定问题与受限项、已执行/未执行的检查和下一落点；验收不足保留未完成状态。
