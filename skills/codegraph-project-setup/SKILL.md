---
name: codegraph-project-setup
description: Use only when the user explicitly asks to enable or prepare CodeGraph for the current project. Based on CodeGraph v1.5.0; safely reviews the Git worktree, merges .trellis/ into codegraph.json, requests confirmation, and then initializes the project index. Never use for ordinary code search or implicit indexing.
---

# CodeGraph 项目启用

此 Skill 是本工作流的项目启用适配器，基于 CodeGraph `v1.5.0`。它只在用户明确要求启用或准备当前项目的 CodeGraph 时使用；不负责全局安装、MCP 注册、上游安装器或日常代码检索。

## 硬性边界

- 当前项目没有明确用户授权时，不运行本 Skill，也不自动建议执行 `codegraph init`。
- 只接受普通主工作树。通过 Git 的 `--git-dir` 与 `--git-common-dir` 判断 linked worktree；发现 linked worktree 立即停止。
- 项目根的 `codegraph.json` 必须保留用户已有字段、`include` 和 `exclude`。至少合并 `.trellis/`；其他排除项只有在实际存在且用户明确批准后才加入。
- 不修改 `~/.codex/config.toml`、任何 `AGENTS.md`、Trellis 工件、OpenViking 数据或 context-mode 数据。
- 不运行 `codegraph install`、`codegraph upgrade`、`codegraph --refresh`，不复制二进制，不创建配置备份。
- 首次 CodeGraph 命令必须带 `DO_NOT_TRACK=1`。主机级部署应已经执行 `DO_NOT_TRACK=1 codegraph telemetry off`；若无法确认，停止并报告，不猜测。

## 工作流

### 1. 解析并检查项目

从当前工作目录调用脚本的只读模式：

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/codegraph-project-setup/scripts/prepare_project.py"
```

脚本会输出 Git 项目根、worktree 类型、当前 `codegraph.json` 状态和拟修改的 unified diff。它的默认模式不写文件。

若脚本报告 linked worktree、不是 Git 项目、`codegraph.json` 不是 JSON 对象、或 `exclude` 不是字符串数组，立即停止。

### 2. 审查排除规则

确认拟议变更至少包含：

```json
{
  "exclude": [".trellis/"]
}
```

不删除、重排或覆盖用户现有的 `include`、`exclude` 或其他 CodeGraph 配置。`.codegraph/` 的排除由 CodeGraph `v1.5.0` 自身和 context-mode 目录保护负责，不把它作为项目业务排除规则的替代品。

### 3. 用户确认后写入

向用户展示脚本输出的完整差异。只有用户确认后，才使用同一项目根执行：

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/codegraph-project-setup/scripts/prepare_project.py" --apply
```

若要增加其他运行目录，必须逐项明确传入：

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/codegraph-project-setup/scripts/prepare_project.py" \
  --extra-exclude '.some-tool/' --apply
```

### 4. 初始化并核验

确认 `/usr/bin/codegraph` 已存在、全局 MCP 已由部署流程人工配置后，从项目根执行：

```sh
env DO_NOT_TRACK=1 codegraph init
env DO_NOT_TRACK=1 codegraph status --json
```

`codegraph init` 只能在当前普通主工作树执行，不向另一个项目传 `projectPath`。初始化失败、状态显示未索引或项目根不符合预期时停止；不自动重试、重建或跨项目查询。

完成后，CodeGraph 只用于当前已批准项目的结构关系查询。首选官方 MCP 工具 `codegraph_explore`，使用单一符号、单一路径或明确的调用关系问题；不要把它当作通用文件阅读、全文检索、任务状态或整仓库问答工具。

## 官方契约兼容性

本 Skill 固定基于 CodeGraph `v1.5.0`。详细源码锚点见 [codegraph-v1.5.0.md](references/codegraph-v1.5.0.md)。必须保持以下官方契约：

- 默认 MCP 工具名为 `codegraph_explore`。
- `codegraph.json` 的 `exclude` 使用 gitignore 风格模式。
- 项目没有 `.codegraph/` 时，不调用 CodeGraph 查询；索引是用户决定。
- `projectPath` 只用于已有索引的 MCP 查询；跨项目实例不附着 watcher，不能当成隔离边界。
- MCP 返回的源码可能有索引滞后提示；出现提示时，直接读取列出的文件确认实时内容。
- CodeGraph 不能替代编译器、测试、lint 或 Trellis 的任务事实。

上游 MCP 初始化指引和上游 `AGENTS.md` marker 不复制到本 Skill。上游指引面向通用 Agent 与原生子代理，而本工作流的全局规则明确不使用 Codex 原生子代理；本 Skill 只承担项目初始化的安全流程。
