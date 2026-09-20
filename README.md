# pennix-skills

用户自维护的 Codex 工作流 Skills 源码。

通用 Trellis Skill 随 Trellis 组件交付；本仓库只维护用户工作流策略、确定性辅助脚本和
对应测试。`skills/windsurf-code-search` 是独立 `windsurf-code-search` 组件的 Git submodule：该组件
继续拥有 CLI、测试和 npm 发布，本仓库只固定其在私有 Skills 组合中的版本。其 npm 包、GitHub
仓库和工作流中的可发现名称统一为 `windsurf-code-search`，不要与 `fastctx` 本地操作运行时混用。

工作流部署统一从 `pennix-workflow-lifecycle` 进入；它只编排内部 deployment adapters，
不接管 Trellis、FastCtx、CodeGraph、Codex Plugin/MCP 或 Hook 的原生所有权。

当前 lifecycle 的宿主边界是 Linux 上的 Arch Linux，包括原生 Arch Linux 和 WSL2
中的 Arch Linux。生命周期包操作优先使用已存在的 `yay`，没有时回退到已存在的 `paru`，最后才使用
`pacman`。Stage 0 的 Codex 最小安装也通过 AUR 的 `openai-codex-bin`：缺少 AUR helper 时会先通过
`pacman` 安装构建前置并 bootstrap `yay`。非 Arch、WSL1 或无法确认 WSL 版本的环境不允许生命周期写入。

## 系统安装：全新 Arch 环境

新环境的首选入口是不预下载源码的远程 seed：

```bash
curl -fsSL https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/scripts/seed-arch.sh | bash
```

当缺少任一 seed 文件时，它下载同一 `main` 上受控的两个静态模板，并从 `/dev/tty` 读取所需交互输入；没有控制终端时会在任何包或配置写入前失败。两份文件均已存在时不需要模板或终端。若本机没有 AUR helper，随后还会检出并构建 `yay` 的 AUR package；它不下载或执行 Pennix 的远端源码。

seed 脚本在源码仓库中的明确位置是：

`skills/pennix-workflow-lifecycle/scripts/seed-arch.sh`

维护和测试本地 checkout 时必须连同相邻模板目录一起使用。在本仓库根目录中可直接复制执行：

```bash
bash ./skills/pennix-workflow-lifecycle/scripts/seed-arch.sh
```

该可执行脚本可从 `bash` 或 `zsh` 启动；脚本通过 Bash shebang 使用所需解释器，
应直接执行，不要使用 `source` 将它加载进调用者 shell。若要复制到其他位置，
请复制整个 `skills/pennix-workflow-lifecycle/` 目录，以保留 `templates/`。

它从官方仓库安装 `npm`、从 AUR 安装当前 `openai-codex-bin`，交互式收集缺失的 `base_url`
或隐藏 API key，根据 `templates/config.toml.seed`、`templates/auth.json.seed` 只物化 seed 阶段字段。已有
`~/.codex/config.toml` 和 `~/.codex/auth.json` 会原样保留；两者都存在时可以无交互重入。
若已安装 catalog 明确登记的旧 `openai-codex` 包，seed 会先通过已选 AUR helper 将其迁移为
`openai-codex-bin`；其他未登记的包不会被猜测或删除。

完成时，seed 会给出一个新 Codex 会话的两轮确定提示。第一轮仅通过系统
`$skill-installer` 将 `pennix-workflow-lifecycle` bootstrap Skill 安装到最终的
`$CODEX_HOME/skills/pennix-skills` 目录；安装器确认成功后不结束该会话，下一轮直接使用该
Skill。它先执行只读 `discover`，识别精确的 `bootstrap` 状态后，按 catalog 的内部合同通过系统
安装器补齐其余 collection，并在同一会话继续部署。系统安装器只使用临时下载，不保留本地仓库副本。

`seed-arch.sh` 没有 `--uninstall`，也不会删除 `auth.json`、`openai-codex-bin`、AUR helper、
构建依赖、Skills、插件或项目资产。凭据文件始终需要用户在轮换或撤销凭据后自行删除。
完整 collection 的安装和升级由系统 `$skill-installer` 在 Codex 会话中拥有；lifecycle 负责
发现、验证，以及仅在目录条目和每个 `SKILL.md` 都完全匹配 catalog 时的精确卸载。更新 collection
时，先由 lifecycle 卸载该单一 component，再在一个新 Codex 会话中按 catalog 的安装合同重装。

`config.toml.install` 只包含工作流必需的静态策略，排除用户 model、sandbox/approval、TUI、Web、
history、主机路径、项目 trust、MCP/插件/marketplace 状态和 hook hash。静态配置和 Agents 模板的
安装、升级、卸载仍由 lifecycle 按单一 component 执行；它不会拼接重复字段或接管其他用户资产。

上游 inspection 只对 catalog 明确登记的 URL 自动执行，发现新的控制面或参数变化会阻断该组件；lifecycle
不会降级为远端脚本执行。安装、升级和卸载都要求明确的单一 component，不生成第二份计划或状态文件。

## 项目初始化

Trellis、CodeGraph 和 AOE 的 CLI 可以由系统生命周期动作部署或升级，但它们的初始化必须在目标项目中
单独执行。lifecycle 不创建 `.trellis/`、`codegraph.json`、索引或项目工作流资产；项目初始化继续使用
各组件的原生命令。卸载全局组件也不会删除项目资产。
