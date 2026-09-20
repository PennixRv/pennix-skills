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

它下载同一 `main` 上受控的两个静态 seed 模板，并从 `/dev/tty` 读取交互输入；没有控制终端时会在任何包或配置写入前失败。若本机没有 AUR helper，随后还会检出并构建 `yay` 的 AUR package；它不下载或执行 Pennix 的远端源码。

seed 脚本在源码仓库中的明确位置是：

`skills/pennix-workflow-lifecycle/scripts/seed-arch.sh`

维护和测试本地 checkout 时必须连同相邻模板目录一起使用。在本仓库根目录中可直接复制执行：

```bash
bash ./skills/pennix-workflow-lifecycle/scripts/seed-arch.sh
```

该可执行脚本可从 `bash` 或 `zsh` 启动；脚本通过 Bash shebang 使用所需解释器，
应直接执行，不要使用 `source` 将它加载进调用者 shell。若要复制到其他位置，
请复制整个 `skills/pennix-workflow-lifecycle/` 目录，以保留 `templates/`。

它从 AUR 安装当前 `openai-codex-bin`，交互式收集 `base_url` 和隐藏 API key，
根据 `templates/config.toml.seed`、`templates/auth.json.seed` 只物化 seed 阶段字段。
它不会覆盖已有 `~/.codex/config.toml` 或 `~/.codex/auth.json`。完成时会输出两 turn 的
确定入口：先在新 Codex 会话中用系统 `$skill-installer` 从
`PennixRv/pennix-skills` 的 `main` 安装唯一 bridge
`skills/pennix-workflow-lifecycle`，在该安装完成后的下一 turn 才使用
`$pennix-workflow-lifecycle`。

首次 bridge 安装后，使用 `$pennix-workflow-lifecycle` 在默认
`$HOME/devel/pennix-skills`（或用户明确选择的路径）创建一个干净的 source checkout，
再安装完整 Pennix Skills collection；不使用远程下载即执行。完整 collection 安装会在且仅在
独立 bridge 与 source 内容完全一致时移除它，避免 Codex 发现重复的同名 Skill；任何漂移 bridge
都会阻断并保留原目录。
`seed-arch.sh` 没有 `--uninstall`，也不会删除 `auth.json`、`openai-codex-bin`、AUR helper、
构建依赖、Skills、插件或项目资产。完整 workflow 的反向操作在 collection 安装后由 lifecycle
逐 component 执行；凭据文件始终需要用户在轮换或撤销凭据后自行删除。
下面的 `--destination` 是当前宿主的默认发现位置；如果宿主使用其他用户级
Skill 发现根，可以显式选择一个以 `skills/pennix-skills` 结尾的目标：

```bash
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  discover
```

随后从明确的本地 checkout 直接执行系统生命周期动作：

`config.toml.install` 只包含工作流必需的静态策略，排除用户 model、sandbox/approval、TUI、Web、
history、主机路径、项目 trust、MCP/插件/marketplace 状态和 hook hash。
安装器只原子替换受管的 `skills/pennix-skills` 目录，并拒绝符号链接路径、非目录目标和未提交 source，
不会拼接重复字段或接管其他用户资产。

```bash
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  install --component pennix-skills --source "/path/to/pennix-skills" --yes
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  install --component codex-config --yes
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  install --component codex-agents --yes
```

已安装组件使用同一个入口升级或卸载：

```bash
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  upgrade --component fastctx --yes
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  uninstall --component fastctx --yes
```

上游 inspection 只对 catalog 明确登记的 URL 自动执行，发现新的控制面或参数变化会阻断该组件；lifecycle
不会降级为远端脚本执行。安装、升级和卸载都要求明确的单一 component，不生成第二份计划或状态文件。

显式选择其他发现根时，将集合根保存到 `PENNIX_SKILLS_ROOT`，再传给 `--destination`：

```bash
PENNIX_SKILLS_ROOT="${PENNIX_SKILLS_ROOT:-$HOME/.agents/skills/pennix-skills}"
python3 "/path/to/pennix-skills/skills/pennix-workflow-lifecycle/scripts/lifecycle.py" \
  install --component pennix-skills --source "/path/to/pennix-skills" \
  --destination "$PENNIX_SKILLS_ROOT" --yes
```

上述系统生命周期 action 只在显式请求时运行。它初始化 checkout 已固定的 submodule，并将每个直接
`skills/<name>/` 物化到所选集合根下的 `<name>/`；未传 `--destination` 时使用
`${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/`。它不新建
源码 checkout、不切换分支、不选择版本，也不更新已固定的组件版本；若本地缺少对象，初始化
submodule 只会取得当前 Gitlink 固定的提交。安装副本不是源码编辑位置，也不生成第二份版本或
状态事实。

## 项目初始化

Trellis、CodeGraph 和 AOE 的 CLI 可以由系统生命周期动作部署或升级，但它们的初始化必须在目标项目中
单独执行。lifecycle 不创建 `.trellis/`、`codegraph.json`、索引或项目工作流资产；项目初始化继续使用
各组件的原生命令。卸载全局组件也不会删除项目资产。
