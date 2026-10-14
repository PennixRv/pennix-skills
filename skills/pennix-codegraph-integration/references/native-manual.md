# 固定版本的原生手册索引

本索引对应 Pennix `1.6.2-pennix.1`。先通过 lifecycle 核验安装版本；原生 `codegraph --help` 和 `<subcommand> --help` 适用于实际安装版本，远程固定版本资料用于对照，不引用研究机器的路径。

| 场景 | 原生入口与说明 |
| --- | --- |
| 安装来源和 fork 边界 | [固定版本 README](https://github.com/PennixRv/codegraph/blob/v1.6.2-pennix.1/README.md)；系统动作交 lifecycle |
| 已批准项目的 MCP/短块配置 | `codegraph install --help`；显式项目根下的 local install；[installer](https://github.com/PennixRv/codegraph/blob/v1.6.2-pennix.1/src/installer/index.ts) |
| 明确授权的项目准备与索引 | `codegraph init --help`、`index --help`；[CLI](https://github.com/PennixRv/codegraph/blob/v1.6.2-pennix.1/src/bin/codegraph.ts)；未授权不执行 |
| 索引状态、陈旧和同步 | `codegraph status --help`、`sync --help`；状态不明不能声称当前图完整 |
| MCP 初始化与查询 | 实际 initialize instructions；[原生 instructions](https://github.com/PennixRv/codegraph/blob/v1.6.2-pennix.1/src/mcp/server-instructions.ts)；不用 Skill 重写协议 |
| 无 MCP 时的受控 CLI 查询 | `codegraph explore --help`；结果回读来源、行号、路径和索引限制 |
| linked worktree / 目录限制 | [目录解析](https://github.com/PennixRv/codegraph/blob/v1.6.2-pennix.1/src/directory.ts)与实际原生回执；本工作流禁止 linked worktree 使用 |
| 更新、刷新与卸载 | `codegraph upgrade --help`、`install --help`、`uninstall --help`；系统替换交 lifecycle，项目块移除仍归原生 target |

源码链接只作为对应版本合同证据。新版本改变入口或能力时更新此索引和治理检查，不把候选版本当作已安装版本。
