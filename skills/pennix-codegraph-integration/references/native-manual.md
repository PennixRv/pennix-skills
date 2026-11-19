# 固定版本的原生手册索引

本索引对应 Pennix `1.6.3-pennix.3`。先通过 Lifecycle 核验实际安装版本；原生 `codegraph --help` 和 `<subcommand> --help` 适用于实际安装版本，远程固定版本资料用于对照，不引用研究机器的路径。索引的发布版本不等于当前宿主已经加载该版本。

| 场景 | 原生入口与说明 |
| --- | --- |
| 安装来源和 fork 边界 | [固定版本 README](https://github.com/PennixRv/codegraph/blob/v1.6.3-pennix.3/README.md)；系统动作交 Lifecycle |
| 已批准项目的 MCP/短块配置 | `codegraph install --help`；显式项目根下使用 `codegraph install --target codex --location local --yes`，不附带 `--init`，索引须另有授权；[installer](https://github.com/PennixRv/codegraph/blob/v1.6.3-pennix.3/src/installer/index.ts) |
| 主动初始化的一次策略 | `pennix config policy --json` 只读策略；具备能力的 `trellis init --codex` 承接已选接入与索引。普通查询不执行此链路；`--project-only` 贯穿原生扫描、同步与 MCP，`init --no-git-hooks` 禁止回退写 Git Hook |
| 明确授权的项目准备与索引 | `codegraph init --help`、`index --help`；[CLI](https://github.com/PennixRv/codegraph/blob/v1.6.3-pennix.3/src/bin/codegraph.ts)；未授权不执行 |
| 索引状态、陈旧和同步 | `codegraph status --help`、`sync --help`；状态不明不能声称当前图完整 |
| MCP 初始化与查询 | 实际 initialize instructions；[原生 instructions](https://github.com/PennixRv/codegraph/blob/v1.6.3-pennix.3/src/mcp/server-instructions.ts)；不用 Skill 重写协议 |
| 无 MCP 时的受控 CLI 查询 | `codegraph explore --help`；结果回读来源、行号、路径和索引限制 |
| linked worktree / 目录限制 | [目录解析](https://github.com/PennixRv/codegraph/blob/v1.6.3-pennix.3/src/directory.ts)与实际原生回执；仅在本树 bound MCP、独立索引和实际 provenance 核验通过时使用；旧版继续禁止借用其他树索引 |
| Codex 分层主动路由 | 原生隐藏入口 `codegraph prompt-hook --agent codex`；[handler](https://github.com/PennixRv/codegraph/blob/v1.6.3-pennix.3/src/codex-prompt-hook.ts)。系统 Hook 定义、原生信任、更新与撤回由 Lifecycle 管理；只读核验真实 `hooks/list`，不手写信任摘要。会话恢复只提示，结构预取仍受本树索引、新鲜度、1250 ms 与 2048 字节限制；`CODEGRAPH_NO_PROMPT_HOOK=1` 或 `CODEGRAPH_PROMPT_HOOK=0` 可关闭该辅助 |
| 更新、刷新与卸载 | `codegraph upgrade --help`、`install --help`、`uninstall --help`；系统替换交 lifecycle，项目块移除仍归原生 target。当前 `install --refresh` 忽略 target 限制并 sweep 全部 target；已选 Codex local 刷新用普通受限 install 重入。仅 `--yes` 默认 global/auto，不能替代精确作用域 |

源码链接只作为对应版本合同证据。新版本改变入口或能力时更新此索引和治理检查，不把候选版本当作已安装版本。
