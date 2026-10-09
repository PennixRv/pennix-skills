# pennix-skills

用户自维护的 Codex 工作流 Skills 源码。

通用 Trellis Skill 随 Trellis 组件交付；本仓库只维护用户工作流策略、确定性辅助脚本和
对应测试。`skills/windsurf-code-search` 和 `skills/grok-search` 是发布集合中的普通目录；其上游
仓库、ref、精确提交和安装后动作由唯一 lifecycle catalog 记录。目标机只接收物化 Skill 集合，
不创建 submodule 或源码 checkout。其可发现名称保持为 `windsurf-code-search` 和 `grok-search`，
不要与 `fastctx` 本地操作运行时混用。

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

远程命令执行指定的 `seed-arch.sh`。缺少任一 seed 文件时，脚本下载同一 `main` 上的两个静态模板，并从 `/dev/tty` 读取所需输入；没有控制终端时，在包或配置写入前失败。两份文件均已存在时不需要模板或终端。缺少 AUR helper 时，脚本检出并构建 `yay` 的 AUR package；它不检出整个 `PennixRv/pennix-skills` 仓库，也不调用完整的 `scripts/lifecycle.py` 入口。

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

完成时，seed 会给出当前 Codex 会话的两轮确定提示，不要求新建会话。第一轮仅通过系统
`$skill-installer` 将 catalog 的 `bootstrap_skill` 安装到最终的
`$CODEX_HOME/skills/pennix-skills` 目录；安装器确认成功后不结束该会话，下一轮直接使用该
Skill。它先执行只读 `discover`；完整安装或升级时，所有 catalog 路径先写入同级 staging，
完成校验后由 `replace-staged` 替换正式 collection。重复执行不会把已存在的 Skill 混入安装器，
也不会创建本地仓库副本。

`seed-arch.sh` 没有 `--uninstall`，也不会删除 `auth.json`、`openai-codex-bin`、AUR helper、
构建依赖、Skills、插件或项目资产。凭据文件始终需要用户在轮换或撤销凭据后自行删除。
完整 collection 的下载仍由系统 `$skill-installer` 拥有；lifecycle 负责发现、staging 完整性验证、
事务替换，以及仅在目录条目和每个 `SKILL.md` 都完全匹配 catalog 时的精确卸载。更新 collection
时不先删除旧目录；只有新 staging 完整匹配后才替换，失败保留旧安装。

`config.toml.install` 只包含工作流必需的静态策略，排除用户 model、sandbox/approval、TUI、Web、
history、主机路径、项目 trust、MCP/插件/marketplace 状态和 hook hash。静态配置和 Agents 模板的
安装、升级、卸载仍由 lifecycle 按单一 component 执行；它不会拼接重复字段或接管其他用户资产。

上游 inspection 只对 catalog 明确登记的 URL 自动执行，发现新的控制面或参数变化会阻断该组件；lifecycle
不会降级为远端脚本执行。安装、升级和卸载都要求明确的单一 component，不生成第二份计划或状态文件。

## 项目初始化

Trellis、CodeGraph 和 AOE 的 CLI 可以由系统生命周期动作部署或升级，但它们的初始化必须在目标项目中
单独执行。lifecycle 不创建 `.trellis/`、`codegraph.json`、索引或项目工作流资产；项目初始化继续使用
各组件的原生命令。卸载全局组件也不会删除项目资产。

## 人工知识与经验

`pennix-siyuan-memory` 按用户意图通过思源原生 MCP 检索、引用、整理、导入和显式保存知识。
它不捕获会话，不替代 Trellis task、正式交接或本地 `trellis mem` 历史；当前源码/任务/spec
仍是工程事实权威。完整晋升方向在 workflow-routing 的 `references/knowledge-promotion.md`，
包括人工经验、项目合同、源码 Skill 和有明确适用范围的全局规则，不要求逐级经过所有库。

连接是可选的 `siyuan-connection` target：先 lifecycle discover，再从操作者自己的终端 configure
该单一目标。从目标思源内核的“设置 → 鉴权 → API token”取得已有值；连接 NAS 时在 NAS 网页中查看，不使用另一独立客户端的 Token。它区别于网页登录密码、模型 API Key 和 S3 密钥，仅在 lifecycle 终端隐藏录入私有文件；原生 header helper 无数据代理逻辑。索引作用域、模型配置和其他客户端同步由思源内核管理，配置成功不能代替原生工具和语义质量验收。

## 中文技术写作

`pennix-chinese-tech-writing` 在本仓库内维护适配版，固定来源和 MIT 许可见该 Skill 的 `UPSTREAM.md` 与 `LICENSE`。它适用于所有新写或修改的中文技术内容，包括用户规则、Skill、Trellis 任务与规范、思源技术笔记；按内容类型加载参考，保留事实、条件、风险和确定程度。只读检查器提供校对建议，不建立样式门禁，也不授权文件修改、任务状态转换或知识保存。
