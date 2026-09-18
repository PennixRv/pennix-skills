# 技术设计：统一 Bootstrap 与内部 Deployment Adapters

## 用户界面

只保留一个用户可见部署 Skill：`pennix-workflow-bootstrap`。它采用 guided 流程，负责
`discover`、`plan`、显式确认后的 `apply`、重新发现后的 `verify` 和受 receipt/hash 保护的
`rollback`。

现有 setup Skill 不再作为并列入口：其脚本、测试和必要参考资料迁移到
`skills/pennix-workflow-bootstrap/scripts/adapters/`。adapter 只能由 bootstrap 调用，不能
自行改变其他组件所有权。

## 单一版本 catalog

`references/component-versions.json` 是唯一静态维护的组件版本文件。它记录 approved
version/ref、来源、owner、scope 和 verify key；所有 adapter、`bootstrap.py`、Skill 文案和
部署文档只引用 component key，不复制具体版本值。`discover` 的 observed version 来自实际
命令/包/plugin 状态，只用于比较并报告 drift，不回写 catalog。

宿主 `/home/penn/.codex/pennix-docs/component-matrix.md` 在集成阶段改为 catalog 的投影或
引用，不再拥有第二份版本事实。任务研究中的当前版本属于带时间戳的 observation，不属于
部署配置；历史版本也不得被重新当作当前目标版本。

## 两阶段启动

Stage 0 是独立的 Arch seed，不依赖 Python、Pennix Skills 或 Trellis：它只使用 Bash（可由
`bash` 或 `zsh` 直接启动，不能 `source`）、`pacman`/`sudo`、已安装的 Codex 和网络，安装 Arch
官方 `openai-codex` 当前候选版本，读取并渲染 `templates/config.toml.seed`、
`templates/auth.json.seed`，只替换用户输入的 `base_url` 和 API key，直接物化最小 provider、
认证和 Default 提问字段。它不调用 Codex 原生登录/feature 写入命令，不下载或执行远程 Pennix
source，不覆盖已有 `CODEX_HOME/config.toml` 或 `auth.json`；发现已有文件即停止。

Stage 0 成功后要求新 Codex session 生效，再由输出的短提示词引导用户安装 Pennix Skills。安装
阶段使用 `templates/config.toml.install` 的根级和 `[features]` 片段以及
`templates/AGENTS.md.install` 物化系统静态字段，
随后由 `pennix-workflow-bootstrap` guided `discover` → `plan` → named `apply` →
`verify`/`rollback`。
Stage 0 的 current candidate 是启动事实，不是固定版本来源；Stage 1 的
`component-versions.json` 仍是唯一静态版本源。

## 目录合同

```text
skills/pennix-workflow-bootstrap/
├── SKILL.md
├── scripts/
│   ├── bootstrap.py
│   └── adapters/
│       ├── skills_install.py
│       ├── fastctx.py
│       ├── trellis.py
│       ├── codegraph.py
│       └── codex_hooks.py
├── references/
│   └── codegraph.md
└── tests/
    ├── test_bootstrap.py
    ├── test_skills_install.py
    ├── test_fastctx.py
    ├── test_codegraph.py
    └── test_codex_hooks.py
```

`workflow-doctor`、`pennix-fastctx-routing` 和 `pennix-workflow-routing` 保持独立，因为它们
分别是诊断和日常路由，不是部署入口。OpenViking、检索、交接和记忆 Skill 不迁入 bootstrap。

## Adapter 边界

- `skills_install.py`：复用现有 source checkout 校验、submodule pin 检查和原子物化。
- `fastctx.py`：复用 FastCtx release checksum、binary apply、guidance marker 和 rollback。
- `trellis.py`：只调用 Trellis native CLI；不复制模板、task schema 或 workflow lifecycle。
- `codegraph.py`：复用普通主工作树、telemetry、`codegraph.json` preview/apply 门禁；项目 index
  仍是可选动作。
- `codex_hooks.py`：复用 Hook fragment validate/merge/migrate；不修改 `[hooks.state]`。

Stage 0 的 provider 配置使用 `requires_openai_auth = true` 和
`cli_auth_credentials_store = "file"`，API key 通过 `auth.json.seed` 模板直接物化到
`CODEX_HOME/auth.json`；key 不写入 `config.toml`、任务、receipt、输出或 Git。已有
`config.toml` 或 `auth.json` 时 Stage 0 不尝试合并，避免覆盖用户 provider、MCP、Hook 和静态
控制面。

系统安装 action 标记为 `system-installation`；Trellis、CodeGraph、AOE 的 CLI 可以由系统 action
部署，但项目初始化 action 标记为 `project-initialize`，必须绑定明确 project root 并单独确认，
不能由 seed 或 Skills installation 隐式执行。

Bootstrap 默认只做全局基线检查和项目可选动作计划；apply 需要显式 action 和 `--yes`，不因
发现到缺失或 degraded 状态就自动修复。

## 宿主与安装器边界

首期只支持 Linux 上的 Arch Linux，宿主分类为 `native` 或 `wsl`。WSL 只有明确识别为
WSL2 才通过写入前置检查；非 Arch、未知 WSL 版本和 WSL1 仍可只读发现，但所有 apply
动作均为 `blocked`。宿主检测读取 `/etc/os-release`、`/proc/sys/kernel/osrelease` 和
`/proc/version`，不读取用户凭据或运行态数据库。

官方仓库安装器固定为 `pacman`；AUR 安装器优先选择已存在的 `yay`，没有时选择已存在的
`paru`。缺少 AUR helper 时不自动从网络获取或执行构建脚本。组件若由上游 release、npm、
Trellis native CLI 或其他 owner 管理，继续使用其 adapter；包名和版本没有官方/AUR证据时，
不进入可执行 action。

guided bootstrap 在 Default 模式使用原生 `request_user_input`（由宿主会话工具清单决定），
或在不可用时使用文本回退；两者都要求提问后停止当前 turn，下一 turn 才可继续。不得把
`request_user_input_async` 当作 Trellis 阻塞门禁，也不默认安装 questionnaire MCP。

决策门规则由独立的 `pennix-decision-gates` Skill 承载；bootstrap 只消费已封存的计划决策。
该 Skill 不包含脚本、MCP 或任务状态修改逻辑。

交互决策只发生在 `clarify`/`research`/`plan`/`plan-check` 或明确的 `grill-me` gate。当前宿主
每批可承载 1–3 个问题；同 gate 且互不依赖的问题合批，答案会改变另一题选项、范围、风险、owner
或验证路径的问题拆批。实现/apply 阶段不临时弹题：已有 task/spec 决策直接执行，影响安全、公开
接口、数据、部署边界或验收的未决灰区记录 `decision-needed` 并回到计划阶段。

能力探测只看当前会话原生工具清单；嵌套工具编排目录（包括 `ALL_TOOLS`）不是原生工具
可用性的证据。原生调用参数错误和宿主能力缺失必须分开记录；前者按 schema 最多重试一次，
后者才进入文本回退，且未得到答案不得自动继续。

## 静态注入

`bootstrap.py` 只通过 adapter 管理用户级 `AGENTS.md` 的 bootstrap-owned marker。marker
操作必须支持 absent/current/drifted/malformed/unowned，保留 marker 外内容，拒绝 symlink、
未知 marker 和 hash 不匹配的 rollback。不得读取或复制 secret、session、database、log、cache、
lock 或完整 `config.toml`/`hooks.json`。

## 命名迁移

用户文档、路由和 seed 命令统一使用 `pennix-workflow-bootstrap`；内部文件使用
`deployment adapters` / `scripts/adapters`，不再使用 `*-setup` 作为运行时发现名称。迁移
过程中不保留同名兼容 Skill，避免 Codex 在旧入口和新入口之间竞争路由。
