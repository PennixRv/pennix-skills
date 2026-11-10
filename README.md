# pennix-skills

这是用户维护的 Codex 工作流 Skills 源码仓库。`collection.json` 是本集合唯一交付
清单，拥有成员路径、许可、命令和物化来源；lifecycle 只固定本仓库提交并验证清单，
不复制成员白名单。组件模板、owner 动作和发行物由独立的
`PennixRv/pennix-lifecycle` 仓库维护。

## 工作流部署

新机先运行独立生命周期工具已核验发行物提供的基础准备脚本，再使用 Kconfig 配置和执行。以下固定为可取得的 `v0.2.28`：

```bash
curl --proto '=https' --tlsv1.2 -fsSLo /tmp/pennix-bootstrap.sh https://github.com/PennixRv/pennix-lifecycle/releases/download/v0.2.28/bootstrap.sh
bash /tmp/pennix-bootstrap.sh install --release v0.2.28
pennix config init
pennix config edit
pennix plan
pennix apply
```

`workflow.config` 是带格式主版本的 Linux Kconfig 文件。`config edit` 和无
TTY 的配置式执行使用同一模型；`pennix secrets edit` 打开权限为 `0600` 的私有
`secrets.toml`，秘密不进入任务、输出、JSON 或 Git。通常通过编辑配置后
`pennix apply` 取消组件；共享用户 Skill 集合取消选择后仍保留，须显式卸载，且会影响同一用户的全部宿主配置。一次性 `pennix uninstall` 不修改配置。

本集合不复制 lifecycle catalog、执行器、模板、暂存、receipt 或组件适配器，也不
通过多轮 Agent 对话引导安装。安装后的 Skill 只描述正确入口和 owner 边界，不在
安装副本形成第二个源码权威。Trellis 任务、Teamwork、交接、Codex 原生登录、插件、
Hook/MCP/TUI、项目初始化和外部检索继续使用各自原生入口。

Codex 自定义 Responses API URL 属于 `workflow.config`，静态 API Key 属于私有 `secrets.toml`；运行时通过 Lifecycle 生成的 `auth.command` 读取 Key。这一路径不要求 ChatGPT 浏览器登录。

`pennix` 支持 Linux Arch 和 Arch WSL2；不受支持或无法证明能力的环境只报告阻断。
服务、自启动、远端 relay、真实网络/付费测试均由配置显式选择；relay 反代策略只依
赖 paseo-relay 仓库文档，Android 配对由用户按 Paseo 原生输出完成。

## Skill 维护

`docx`、`pdf`、`pptx`、`xlsx` 是 Anthropic 官方固定提交的本地衍生版本，使用各自 Apache 2.0 许可。来源、文件比较及本地适配见各自 `UPSTREAM.md`。默认入口用于本地阅读；Python、OCR 和 Office 转换依赖由 Lifecycle 管理，Skill 不临时安装包，也不自动改写原件。完整生成方法保留，但不代表生成依赖已经安装或全面验收。

`pennix-windsurf-code-search` 和 `pennix-grok-search` 是发布集合中的物化目录；其
上游源码和固定提交由 `collection.json` 声明。项目 AGENTS
治理、CodeGraph 集成、中文技术写作、Context Mode 集成和知识操作继续由对应 Skill 负责。

本仓的 `skills/<name>` 是源码路径；安装后的集合层级和 Skill 声明路径由宿主提供。加载时保留主集合、extra 集合或项目 Skill 的实际目录，相对引用从实际 `SKILL.md` 所在目录解析，不按名称猜测平铺路径。

共享集合安装在 `$HOME/.agents/skills/pennix-skills` 和 `$HOME/.agents/skills/pennix-skills-extra`；`CODEX_HOME` 继续管理 Codex 配置，不切换共享集合版本。旧目录通过 Lifecycle 的同版本 `repair` 迁移，再用 `update` 升级内容；不要手动移动安装树或 receipt。

维护时运行 `python3 scripts/collection.py verify`；同步工作流先用 `python3 scripts/collection.py sources` 验证并读取固定来源，按声明的 `archive` 或 `npm-pack` 模式生成目录，再验证完整集合。修改先进入真实来源仓库，物化目录不直接编辑。集合、各 Skill 与 `evaluations/` 的离线测试分别运行；离线检查不代表模型实际路由通过。

`pennix-siyuan-knowledge` 只在用户明确要求时通过思源原生 MCP 检索、整理、导入或
保存知识；它不替代 Trellis task、正式交接或 `trellis mem` 历史。
