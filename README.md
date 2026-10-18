# pennix-skills

这是用户维护的 Codex 工作流 Skills 源码仓库。`collection.json` 是本集合唯一交付
清单，拥有成员路径、许可、命令和物化来源；lifecycle 只固定本仓库提交并验证清单，
不复制成员白名单。组件模板、owner 动作和发行物由独立的
`PennixRv/pennix-lifecycle` 仓库维护。

## 工作流部署

新机先运行独立生命周期工具发行物提供的基础准备脚本，再使用 Kconfig 配置和执行：

```bash
curl --proto '=https' --tlsv1.2 -fsSLo /tmp/pennix-bootstrap.sh https://github.com/PennixRv/pennix-lifecycle/releases/latest/download/bootstrap.sh
bash /tmp/pennix-bootstrap.sh install
pennix config init
pennix config edit
pennix plan
pennix apply
```

`workflow.config` 是带格式主版本的 Linux Kconfig 文件。`config edit` 和无
TTY 的配置式执行使用同一模型；`pennix secrets edit` 打开权限为 `0600` 的私有
`secrets.toml`，秘密不进入任务、输出、JSON 或 Git。永久取消组件通过编辑配置后
`pennix apply` 完成；一次性 `pennix uninstall` 不修改配置。

本集合不复制 lifecycle catalog、执行器、模板、暂存、receipt 或组件适配器，也不
通过多轮 Agent 对话引导安装。安装后的 Skill 只描述正确入口和 owner 边界，不在
安装副本形成第二个源码权威。Trellis 任务、Channel、交接、Codex 原生登录、插件、
Hook/MCP/TUI、项目初始化和外部检索继续使用各自原生入口。

`pennix` 支持 Linux Arch 和 Arch WSL2；不受支持或无法证明能力的环境只报告阻断。
服务、自启动、远端 relay、真实网络/付费测试均由配置显式选择；relay 反代策略只依
赖 paseo-relay 仓库文档，Android 配对由用户按 Paseo 原生输出完成。

## Skill 维护

`pennix-windsurf-code-search` 和 `pennix-grok-search` 是发布集合中的物化目录；其
上游源码和固定提交由 `collection.json` 声明。项目 AGENTS
治理、CodeGraph 集成、中文技术写作、Context Mode 集成和知识操作继续由对应 Skill 负责。

`pennix-siyuan-knowledge` 只在用户明确要求时通过思源原生 MCP 检索、整理、导入或
保存知识；它不替代 Trellis task、正式交接或 `trellis mem` 历史。
