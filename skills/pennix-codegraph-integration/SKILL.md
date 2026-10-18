---
name: pennix-codegraph-integration
description: 配置或使用已批准项目的 CodeGraph，核对 MCP/CLI 入口、索引状态与工作树限制，并导航到固定 fork 的原生手册；不执行系统部署、不治理整个 AGENTS 文件、不自动启用索引。
---

# CodeGraph 集成

Pennix 受限 fork 保持 `codegraph` CLI，交付 Linux x64 的 `@pennixrv/codegraph` 与同版本平台包。系统包、版本和 AUR 迁移用 `$pennix-component-lifecycle`；项目文件的来源、冲突和手工正文用 `$pennix-project-agents-governance`。本 Skill 提供使用边界和手册索引，不复制查询状态机或完整 MCP 协议。

Codex 主会话和 Trellis 独立 Codex 节点是功能保障范围。全局 install/refresh/upgrade/uninstall 保留用户级 AGENTS 原文；用户层仅保留本 Skill 的一行导航。已批准项目可通过原生 local install 维护短块，块只提示能力条件和 MCP/CLI 入口。其他宿主只保留已核验兼容行为，不推导相同功能保证。

先确认明确项目根、当前 cwd、工具是否实际暴露、CLI 来源与原生索引状态。索引存在不等于已批准使用；根目录缺少 `.codegraph/` 也不能单凭字面条件判定子项目无能力。linked Git worktree 不使用 CodeGraph。缺少能力、未索引或陈旧时报告限制并使用有界源码证据，不隐式安装、初始化、sync 或重建索引。

只在宿主实际提供原生 MCP 工具时调用；deferred 工具沿宿主发现入口加载。MCP initialize instructions 和原生 help 是协议权威。结构、调用、影响范围问题可用 CodeGraph；本地文本分析与普通 CLI 按 `$pennix-context-mode-integration` 选择载体，精确编辑依据完整读取。关键结论回到当前文件核验，图输出不自动晋升为任务事实。主会话和独立节点各自核验能力，不能以主会话工具可见代替节点验收。

需要项目准备、配置或协议细节时读[原生手册索引](references/native-manual.md)。调用形式或本地可执行位置不改变组件原生接口要求。实际操作保留原始成功、受限和错误结果；不以第二套重试器、缓存或自动索引掩盖缺口。
