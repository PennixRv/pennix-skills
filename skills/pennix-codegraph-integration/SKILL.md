---
name: pennix-codegraph-integration
description: 已批准且索引可用项目的符号、调用、依赖、具名流程和影响问题优先使用 CodeGraph；核对 MCP/CLI、索引及工作树边界，导航原生手册。不负责语义候选、系统部署或自动索引。
---

# CodeGraph 集成

Pennix 受限 fork 保持 `codegraph` CLI，交付 Linux x64 的 `@pennixrv/codegraph` 与同版本平台包。系统包、版本和 AUR 迁移用 `$pennix-component-lifecycle`；项目文件的来源、冲突和手工正文用 `$pennix-project-agents-governance`。本 Skill 提供使用边界和手册索引，不复制查询状态机或完整 MCP 协议。

Codex 主会话和 Trellis 独立 Codex 节点是功能保障范围。全局 install/refresh/upgrade/uninstall 保留用户级 AGENTS 原文；用户层仅保留本 Skill 的一行导航。已批准项目可通过原生 local install 维护短块，块只提示能力条件和 MCP/CLI 入口。其他宿主只保留已核验兼容行为，不推导相同功能保证。

先确认明确项目根、当前 cwd、工具是否实际暴露、CLI 来源与原生索引状态。索引存在不等于已批准使用；`projectPath` 会解析其自身或祖先最近的 `.codegraph/`，不是子目录过滤器，根目录缺少索引也不代表子项目无能力。linked Git worktree 不使用 CodeGraph。缺少能力、未索引或陈旧时报告具体限制，在 Context Mode 内补有界当前源码证据，不隐式安装、初始化、sync、重建索引或转外部影响分析。

符号、模块、调用、依赖、具名流程、架构和影响／测试线索问题优先使用可用图；它按名字和代码词检索，接收自然语言不代表业务语义向量检索。已知路径／字面量的精确读取匹配默认在 Context Mode 内完成；明确语义定位但无代码锚点时见 `$pennix-windsurf-code-search`，完整路由表归 `$pennix-workflow-routing`。

只在宿主实际提供原生 MCP 工具时直接调用，不通过 Context Mode 模拟；deferred 工具沿宿主发现入口加载。真实等价 CLI 默认按 `$pennix-context-mode-integration` 承载。MCP initialize instructions 和原生 help 是协议权威。实际返回且当前有效的源码区段可复用，不为“回到源码”机械重复读取；未返回部分、陈旧数据、强制全文及必要正确性检查须补齐当前证据，图关系不自动晋升为任务事实。主会话和独立节点各自核验能力，不能以主会话工具可见代替节点验收。

需要项目准备、配置或协议细节时读[原生手册索引](references/native-manual.md)。调用形式或本地可执行位置不改变组件原生接口要求。实际操作保留原始成功、受限和错误结果；不以第二套重试器、缓存或自动索引掩盖缺口。
