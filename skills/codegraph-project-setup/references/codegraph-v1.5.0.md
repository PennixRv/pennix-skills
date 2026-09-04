# CodeGraph v1.5.0 契约摘要

本 Skill 固定参考 CodeGraph `v1.5.0`，不是可变的 `main` 分支。部署前若升级 CodeGraph，必须重新核对以下源码锚点并更新本文件。

## MCP

- `src/mcp/tools.ts`：默认 MCP 面只有 `codegraph_explore`；最终返回上限为 15,000 字符。
- `src/mcp/server-instructions.ts`：MCP 初始化指引分为有默认项目索引和无默认项目两种情况。无默认项目时，查询已有索引需要绝对 `projectPath`；没有索引的项目不应调用 CodeGraph。
- `src/mcp/tools.ts`、`src/mcp/engine.ts`：省略 `projectPath` 时使用会话默认项目；显式跨项目查询打开缓存实例，不附着默认 watcher；无默认项目时工具 schema 会把 `projectPath` 标为必填。

## 项目配置与初始化

- `src/project-config.ts`：`codegraph.json` 的 `exclude`、`include` 和 `includeIgnored` 使用 gitignore 风格模式，并参与索引、同步和 watcher。
- `src/index.ts`：`CodeGraph.init(projectRoot, ...)` 在项目建立 `.codegraph/`；CLI 的 `codegraph init` 使用同一初始化语义，它不是 MCP 注册命令。
- `src/sync/worktree.ts`：从调用目录向父目录解析最近的 `.codegraph/`；嵌套或 linked worktree 可能读到另一分支的图，只有 warning 不会自动阻断。

## Agent 注入

- `src/installer/targets/codex.ts`：Codex 安装器只支持 global 目标，会替换自己拥有的 `[mcp_servers.codegraph]` 表。
- `src/installer/instructions-template.ts`：安装器写入 marker-fenced `AGENTS.md` 区块，主要覆盖没有 MCP 初始化指引的原生子代理或非 MCP harness。

本工作流不运行该安装器，也不复制该 marker。全局 `AGENTS.md` 只保留项目条件、边界和 Skill 入口；MCP 初始化指引由 CodeGraph 服务自己提供。

## 版本更新门禁

以下任一项变化都需要重新审查 Skill：`codegraph_explore` 名称或参数、`projectPath` 解析方式、`codegraph.json` schema、worktree 查找逻辑、MCP 默认工具面、遥测初始化路径。

源码来源：

- <https://github.com/colbymchenry/codegraph/tree/v1.5.0/src/mcp>
- <https://github.com/colbymchenry/codegraph/blob/v1.5.0/src/project-config.ts>
- <https://github.com/colbymchenry/codegraph/tree/v1.5.0/src/installer>
