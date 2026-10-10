---
name: pennix-workflow-lifecycle
description: 仅在用户明确要求检查、安装、升级、卸载或核验工作流组件时使用的工作流生命周期入口。
metadata:
  short-description: 安全管理工作流生命周期
---
# 工作流生命周期
仅在用户明确请求工作流部署时使用。本 Skill 是面向用户的唯一部署入口；组件设置逻辑由内部适配器负责。
生命周期管理配置意图和就绪状态，不管理共享密钥。组件清单（catalog）声明有限的配置目标，私有配置记录只保存操作者选择了哪些可选目标。秘密值必须留在私有所有者记录或所有者控制的终端流程中。不得创建共享 `.env`，不得把值写入聊天、任务资产、参数、环境变量或清单输出，也不得把一个组件的凭据复制到另一个组件。

## 两类工作

生命周期必须把系统安装和项目初始化分开显示、计划和确认。系统安装可以部署全局工具，但不初始化任何特定项目；项目初始化必须携带明确的 `project root`，并单独确认。

### 系统安装

在 Codex 或 `pennix-skills` 集合尚不存在的全新 Arch Linux 主机上，优先使用远程种子入口：

```bash
curl -fsSL https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/scripts/seed-arch.sh | bash
```

任一种子文件缺失时，远程入口通过 HTTPS 获取两个静态模板，并从 `/dev/tty` 读取所需回答；没有控制终端时在写入包或配置前失败。两个文件都已存在时不需要模板或终端。没有 AUR 辅助程序时，还会检出并构建 `yay` AUR 包。它不会克隆 `PennixRv/pennix-skills`，也不会调用完整的 `scripts/lifecycle.py` 入口；远程命令只执行指定的 `seed-arch.sh`，并且只在需要时获取静态模板和构建 `yay`。

维护和离线夹具测试可以从 `bash` 或 `zsh` 启动；脚本的 Bash shebang 选择所需解释器。把它作为命令执行，不要 source 到调用者 Shell。本地种子读取相邻的 `templates/` 目录；迁移时复制整个 `pennix-workflow-lifecycle` 目录。

它支持原生 Arch Linux 和 WSL2 中的 Arch Linux。通过官方仓库安装 `npm`，通过 AUR 安装当前的 `openai-codex-bin` 候选；仅在缺少 OpenAI 兼容 `base_url` 或隐藏 API key 时提问，渲染受跟踪的 `templates/config.toml.seed` 和 `templates/auth.json.seed`，并只将种子所有的缺失文件写入 `CODEX_HOME`。已有文件逐字保留，因此两者都已存在时种子可重入且不再提问。若组件清单授权的旧 `openai-codex` 包已安装，种子通过选定 AUR 辅助程序迁移到 `openai-codex-bin`；不会猜测或删除未列入清单的包所有者。

种子不克隆 `PennixRv/pennix-skills`，不调用完整生命周期入口，不把密钥写入 TOML、不输出密钥，也不把当前包候选加入固定组件清单。它不接受参数；`seed-arch.sh --uninstall` 必须在任何写入前拒绝。

完成输出对应当前 Codex 会话的下一轮用户输入，不要求新会话。第一轮只通过系统 `$skill-installer` 安装清单中的 `bootstrap_skill`。安装器会说明新 Skill 在下一轮可用；下一轮仍在同一会话中调用本 Skill。

下一轮先运行只读 `discover`。若 `pennix-skills` 状态为 `bootstrap` 或 `partial`，读取 `references/component-versions.json` 中的 `missing_skills` 和唯一的 `collection_contract`。完整安装或升级时，在 `$CODEX_HOME/skills` 下创建新的相邻暂存目录，用 `$skill-installer` 安装清单列出的全部 Skill 目录；不得直接安装到活动集合。该集合使用安装器的 `--method git` 模式（或保留仓库文件模式的等效模式），因为可执行的 `seed-arch.sh` 在只下载暂存时可能变成 `0644`。安装器调用只能使用清单中定义的源路径；物化条目提供来源和封闭的安装后元数据。

替换前核对暂存树恰好包含清单声明的 Skill 名称、有效 frontmatter 和可执行的 `seed-arch.sh`，然后从已核验的暂存树运行原生入口，使清单和相邻模板属于同一版本；不要把新清单注入旧入口。Skill 接纳要求 PyYAML（Arch 包名为 `python-yaml`）；`discover` 报告解析器就绪状态，不静默安装，也不回退到正则校验。如果 AGENTS 模板有变化，集合替换期间保留旧完整文件，再使用新入口显式执行 `upgrade --component codex-agents --yes`。只有已知的完整旧模板可以迁移；未知本地内容必须停止。

```bash
python3 <staged-lifecycle>/scripts/lifecycle.py replace-staged \
  --component pennix-skills --staging "$CODEX_HOME/skills/.pennix-skills-stage" \
  --destination "$CODEX_HOME/skills/pennix-skills" --yes
```

`replace-staged` 只运行清单声明的安装后动作 ID，为最终树创建私有完整性收据，并拒绝未知或已漂移的活动内容。明确确认的 `replace-staged --yes` 可以一次性接纳没有收据的精确旧集合；这是一次性的收据建立且仍是事务性操作。自动刷新和卸载拒绝旧的或已漂移的完整集合。暂存校验、准备或替换失败时保留活动内容。缺失或部分清单集合可重入；用户创建的目录从不删除。有限的清单命令映射只有在目标不存在或已由匹配收据证明时才安装到 `~/.local/bin`；无归属文件、链接、其他集合目标或 PATH 遮蔽都会阻塞操作。若 `~/.local/bin` 不在 PATH，`discover` 只报告前置条件，不修改 Shell 启动文件。替换后再次运行 `discover` 和 `verify`。不要在提示或文档中重新抄写并行 Skill 列表。

没有收据的 `.pennix-skills-stage*` 条目不算完成安装，也不算生命周期所有的状态。`discover` 只报告其直接子项名称（已脱敏）和 `unknown` 状态；不读取内容、不推断年龄、PID、进程、会话或来源，也不删除或接管。该提示不阻塞生命周期所有组件的核验；清理必须另行明确授权。

集合收据不把 Python 可再生的 `__pycache__` 目录和 `.pyc` 文件纳入摘要。这些是运行缓存，不是受管 Skill 内容；其他文件、模式、目录和符号链接检查仍属于完整性合同。

支持的主机边界是 Linux 上的 Arch Linux，包括原生 Arch Linux 和 WSL2 中的 Arch Linux。包操作优先使用已安装的 `yay`，其次 `paru`，最后 `pacman`。第 0 阶段 Codex 安装也遵循此 AUR 路径：两个辅助程序都不存在时，通过 `pacman` 安装 `base-devel` 和 `git`，再从 AUR 构建 `yay`，最后安装 `openai-codex-bin`。生命周期本身不安装 AUR 辅助程序、不猜测包名，也不通过包管理器强行处理独立或 fork 组件。非 Arch 主机以及未知或 WSL1 环境可以发现，但所有写操作均阻塞。

种子完成后，系统安装直接走：`discover` → `install|configure|upgrade|uninstall --component <name> --yes` → 全新 `verify`。`discover` 只读报告清单目标、观察到的版本、实际包所有者和仓库候选，不修改清单也不应用候选。`verify --component <name> --yes` 只核验指定组件及其完整性和上游合同；未知组件报错，不回退到完整核验。`verify --yes` 是完整工作流基线，也核验核心和已启用配置目标。两种形式都返回含 `scope`、`checked_components`、`failures` 和 `advisories` 的 `verification` 结构化对象；只有 `failures` 产生阻塞状态和退出码。可读的已安装版本落后于可读仓库候选时，只对 `repository-latest` 包报告 `upgrade-available` 提示；缺失、未知、所有者不安全、固定版本漂移、静态漂移和必需就绪缺失仍是阻塞。

`pennix-skills` 是安装集合，不是静态组件：安装和升级属于系统 `$skill-installer`；生命周期发现清单声明的精确入口集合、收据状态，并且只卸载与收据匹配的精确集合。`bootstrap` 是精确的单 Skill 初始形状；`partial` 是有效 frontmatter 且明确列出 `missing_skills` 的安全的清单成员子集。二者都按上述同一会话流程继续；无关入口、无效 frontmatter、旧完整集合和未知内容都阻塞，不能自动修复或删除。

`codex-config`、`codex-agents` 和 `tmux-config` 是受支持的静态组件。静态资产独立于敏感配置目标，按各资产合同使用受跟踪模板、受管块、单资产完整性收据和漂移即停止的处理；不读写私有配置档或共享 `.env`。`codex-config` 在所有生命周期值语义存在时接受已有配置为 `compatible`，并保留额外用户值。`codex-agents` 从唯一源模板管理整个用户级 `AGENTS.md`，不使用 begin/end 块或个人扩展区。个人规则变化属于该源模板。仅激活本 Skill 不会写入静态资产。安装只创建缺失文件；显式升级只原子替换已核验的完整旧版本；卸载只删除当前版本或已知旧版本的精确文件。未知内容、不安全所有者、权限或符号链接会被保留并阻塞。物化模板状态与实际生效指令来源分开：非空 `AGENTS.override.md` 会遮蔽 `AGENTS.md`，保留不动，并阻止声称受管规则已生效；空覆盖文件忽略。诊断遵守 `CODEX_HOME`。

`tmux-config` 是明确的组件操作，只管理 `HOME/.tmux.conf` 中的 Pennix 块。基线包括 `default-terminal`、真彩色 `terminal-overrides` 和成对的 tmux 窗口前景或背景样式。它不管理 CCH 块、CCH 运行态文件、状态栏布局、Shell 启动文件、用户快捷键或项目资产。安装或集合替换不会隐式写入该块；使用 `discover` 和 `verify` 分别查看静态资产状态和包安装或配置就绪状态。

组件清单还包含 `pennix-workflow-state`，这是只管理状态的组件，唯一动作是明确的旧状态协调。它把生命周期私有档和静态收据放在 `${XDG_STATE_HOME:-~/.local/state}/pennix-workflow-lifecycle/homes/<sha256(CODEX_HOME)>` 下；解析后的 `CODEX_HOME` 只以命名空间摘要表示。活动 Skill 集合收据位于活动集合旁；原生安装器暂存目录和凭据仍由各自所有者负责。静态记录与敏感配置记录是分离合同，不合并到共享 `.env`。

配置模板只是可移植静态基线：不包含主机路径、项目信任、Web 位置、MCP 或插件状态、Marketplace 状态、Hook 摘要以及用户模型、安全、界面或历史偏好。清单中的包操作只安装匹配的固定候选；`codex-cli` 例外，跟随当前 AUR 仓库候选。`replaces` 是已知包所有者迁移的完整允许列表，例如将无范围的 `fastctx` npm 包迁移到 `@pennixrv/fastctx`；旧所有者通过同一原生包管理器移除。未列入或无法核验的命令所有者阻塞，绝不自动删除。插件操作使用 Codex 原生插件生命周期；Marketplace 不存在或其 Git `HEAD` 精确解析到清单引用时才允许操作。引用无法核验时阻塞而不修改。后续插件添加失败时，只有原生清单证明刚创建的 Marketplace 中没有安装插件，生命周期才删除它；状态不明必须保留并由所有者恢复。

FastCtx 不物化或刷新用户 `AGENTS.md`；其 Apply 和 TUI 路径都不触碰该文件。由 `PennixRv/pennix-skills` 维护的 `skills/pennix-workflow-lifecycle/templates/AGENTS.md.install` 是唯一的工作流用户规则来源，由 `codex-agents` 物化。

### Trellis/CCH 会话计费升级核验

先 discover，并按清单固定版本选择 `trellis-cli` 的 upgrade 或 verify；开始前确认相关 Channel 的已派节点和预留槽位均已排空，不为升级擅自终止工作节点。项目资产逐个绑定明确根目录，由 `$pennix-trellis-project-update` 更新并保留原工作流。

CCH 安装或升级仍使用其原生安装接口：从固定 GitHub Release 下载官方包并核对 checksum，更新 discover 确认的包落点，再执行原生 install 刷新受管运行态。核对包、CLI、运行态版本与渲染器字节一致，并核对端点、令牌和不受管的 tmux 正文在升级前后不变；只报告比较结果，不输出秘密。

Trellis 公共 `channel sessions --owner-session <id> --json` 是历史 Codex 后代成员来源。关系元数据从启用新绑定后开始保留，不导入旧历史；用公开的 `trackingSince` 和 `coverage` 明确边界。最小关系记录不是可删除的临时 Channel 日志或 CCH 缓存；不得通过保留原始日志或读取内部关系文件补造完整账单。安装核验须运行真实 status render：无活动节点、Channel 清理、任务或 cwd 切换后历史仍参与；部分已知金额包括零值正常累计，只有全部有用量而没有金额时才显示问号。本地隔离夹具可以核验协议；真实现场只读核验，不为测试新派付费节点。

### 配置目标

当相关交付组件为 `match` 后，使用明确的目标 ID：

```bash
python3 <installed-lifecycle>/scripts/lifecycle.py configure \
  --component <target-id> --yes
```

`discover` 报告清单中每个目标的掩码就绪状态以及是否启用。`codex-provider` 是唯一核心目标，交给原生 `codex login` 终端流程；官方文档将浏览器登录称为默认路径。每个可选目标只有在明确执行过 configure 后才启用，因此后续 verify 只核验选定集成，不要求每台主机都运行无关服务。

组件清单定义 `cch-connection`、`hikari-connection`、`grok-search-provider`、`grok-tavily-extra`、`windsurf-credential` 和 `siyuan-connection`。思源笔记令牌在目标内核的 `设置 → 鉴权 → API token` 中取得；连接 NAS 时从 NAS Web 客户端取得，独立桌面内核有自己的令牌。思源笔记默认生成令牌，应复用现有值，除非有意轮换。它与 Web 登录密码、模型服务商 API 密钥和对象存储凭据不同。可选目标使用隐藏终端输入、私有所有者记录和 Codex 原生请求头辅助程序；本地就绪不证明服务器握手或索引范围。原生运行核验见 `pennix-siyuan-memory/references/connection-and-index.md`。CCH 和 Windsurf 交给各自所有者的 configure 命令。Hikari 和 Grok 只从 `/dev/tty` 接收值，隐藏秘密输入，并写入私有所有者记录。Grok 拒绝覆盖缺少其生命周期标记的记录。交付先匹配，集合目标还要求匹配的完整性收据。

生命周期不再公开或配置已经退役的 Firecrawl 目标。明确的 `reconcile` 只能在验证后，从带生命周期标记的 Grok 私有记录移除退役字段、目标选择和精确的旧冷却文件。服务商凭据、Tavily 设置、运行记录和无关缓存保持不动；记录不安全或状态不明时停止。

私有档保存在生命周期 XDG 状态命名空间，权限为 `0600`，只含目标 ID 和规范化配置合同摘要，可以安全重建。普通组件版本更新保留它。配置合同变化时，`discover` 标记为 `stale`；再次执行相关 configure 以重新封存。verify 要求核心目标和所有启用的可选目标处于 ready 或 configured 状态，但绝不输出秘密、秘密路径或配置值。

对已有的 `CODEX_HOME/pennix-workflow-lifecycle` 树，先运行只读 `discover`。精确允许列表记录安全时，明确确认的迁移是：

```bash
python3 <installed-lifecycle>/scripts/lifecycle.py reconcile \
  --component pennix-workflow-state --yes
```

协调会在原子复制前核验全部源和目标记录，在写入核验后只删除精确旧记录；冲突、不安全项或失败时保留旧树。它从不递归清理或迁移凭据。

### 上游安装器与提问

对于清单声明 `upstream_inspection` 的组件，`install` 和 `upgrade` 会在调用组件原生安装接口前读取清单指定的 HTTPS 文本，限制大小、计算 SHA-256，并用组件专属解析器检查已知安装控制面；绝不执行下载内容。`upstream-contract-changed` 或 `unavailable` 会阻断该组件，不得以继续执行上游脚本绕过。

提问候选只来自清单的 `decision_profile` 和 inspection 已知语义。已有工作流偏好、可以唯一推导的包管理器、固定版本以及不适用于选定交付方式的上游选项直接记录而不提问。只有互斥答案会改变范围、安全、成本、外部行为或验收，并且每个答案都能映射到已审阅的适配器动作时才提出中文问题。例如 AoE 默认交付是 AUR 包，因此上游 `INSTALL_DIR` 不适用，不生成该问题。

### 项目初始化

Trellis、CodeGraph 和 AOE 二进制可以按目录组件键安装或升级，但项目初始化始终是独立的原生操作。系统生命周期命令不得顺带创建 `.trellis/`、`codegraph.json`、索引或项目工作流资产。

原生项目初始化前确认绝对项目根目录，并将宿主命令的 `workdir` 设置为该根目录。`trellis init` 使用进程 cwd；生命周期参数不会绑定它。应在确认项目中将 `workdir` 设置为该根目录后调用 `trellis init`，不要从其他 Shell 目录执行。生命周期没有 `--project-root` 参数，也不会代用户运行初始化器。已有项目的原生 Trellis 资产更新或明确的工作流刷新使用 `$pennix-trellis-project-update`；生命周期不替代该项目归属流程。

执行直接生命周期命令前，展示组件键、清单来源或引用、目标、风险和预期所有者操作。当前会话有宿主原生 `request_user_input` 时直接使用它。不得替换为 `request_user_input_async`，不得增加 Agent 等待期限，也不得用经过时间推断回答。等待生命周期属于宿主；不要声称可配置不受支持的超时。必须回答而未回答的决策会阻塞依赖操作；更高优先级的宿主规则约束可选问题。重要规划选择使用 `$pennix-decision-grill`。不得通过 `functions.exec`、嵌套 `tools.*`、`ALL_TOOLS`、Shell 或 MCP 探测它。Schema 错误最多修正并重试一次；宿主拒绝、取消、超时或原生交互不可用时退回文本并停止本轮。如果答案在同一原生继续中到达，持久化决策、重新评估依赖门禁并继续当前生命周期流程；不要因为刚提出问题就结束本轮。不得自动选择推荐项。宿主允许时合并同一门禁中相互独立的决策；有依赖的决策分开提问。实施期间复用已封口任务或规范决策；出现重要新选择时记录 `decision-needed`、停止依赖操作，并按当前任务原生重规划合同使用 `$pennix-decision-grill`。同范围、低风险的增量无需重复批准。

所有组件版本、引用、配置目标和封闭安装后动作 ID 都来自 `references/component-versions.json`。不要在本 Skill 或适配器中增加第二张版本表。不得输出秘密值、完整配置、会话、数据库、日志、缓存、锁或运行态。`uninstall` 只通过原生接口移除精确的生命周期文件、精确的 `pennix-skills` 集合或包或插件；漂移内容留存不动。第 0 阶段没有卸载模式，也不移除 `auth.json`、Codex 包、AUR 辅助程序、构建依赖、完整 Skills、插件或项目资产。集合到位后，每次只卸载一个明确的生命周期组件；手动移除 `auth.json` 前先撤销或轮换凭据。
