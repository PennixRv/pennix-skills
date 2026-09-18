# 实现统一 Pennix Workflow Bootstrap

## Goal

实现统一 guided bootstrap Skill，并将现有用户可见 setup Skill 收敛为内部 deployment adapters；保留原生组件边界、分阶段静态模板合同和可验证的 discover/plan/apply/verify/rollback。

## Requirements

- 只提供一个用户可见的 `pennix-workflow-bootstrap` guided Skill；现有 `pennix-fastctx-setup`、`pennix-trellis-setup`、`codegraph-project-setup` 和 `pennix-skills-install` 不再作为独立 Skill 被发现。
- 将上述 setup 能力的确定性脚本、测试和必要 reference 迁移到 `skills/pennix-workflow-bootstrap/scripts/adapters/`，保留原生 owner、确认门禁、失败关闭和回滚语义。
- 新入口实现 `discover`、`plan`、显式确认后的 `apply`、`verify` 和 receipt/hash 保护的 `rollback`；默认显示项目可选动作但不自动 apply。
- 从全新 Arch 环境开始必须有独立的 Stage 0 seed：安装 Arch 官方 `openai-codex` 当前候选版本，读取仓库内提取的 `config.toml.seed`/`auth.json.seed` 模板，交互式替换 `base_url` 和隐藏 API key，直接物化 `CODEX_HOME/config.toml`、`auth.json` 及 Default 提问字段；不得调用原生登录或 feature 写入命令。
- 组件目标版本、发布 ref、来源、owner、作用域和验证 key 只能维护在 `references/component-versions.json`；其他 Skill、adapter、README、测试说明和宿主矩阵不得重复声明具体组件版本。
- `discover` 只能读取实际环境并报告 observed version；它必须区分 catalog `match`、`drifted`、`missing` 和 `unknown`，不得把实际版本写回静态文件。
- 用户级 `AGENTS.md` 只允许在目标不存在时由完整安装模板显式物化；`config.toml` 只允许 seed/install
  模板声明的可移植静态字段。不得复制 secrets、sessions、数据库、logs、cache、locks、主机路径、项目
  trust、MCP/插件状态或 `[hooks.state]`。
- seed 采用显式 source checkout + 受控脚本；apply 逐项确认；Codex 配置只允许白名单 key；catalog unknown 失败关闭；项目动作只计划不自动执行；提问后立即停 turn。
- 交互工具必须从当前会话原生调用面直接调用；`ALL_TOOLS`/嵌套 `tools.*` 只用于脚本编排，不得用于能力探测或替代原生交互；schema 错误最多修正重试一次，宿主拒绝/取消/超时才允许文本回退。
- 交互回退固定为文本回退并停；不得因调用层误用自动切换 MCP 或自动选择推荐项。
- 首期宿主严格限定为 Linux 上的 Arch Linux，覆盖原生 Arch Linux 与 WSL2；官方仓库包使用 `pacman`，AUR 包优先使用已存在的 `yay`，没有时才回退到 `paru`。
- 非 Arch、WSL1 或无法确认 WSL2 的环境可以执行只读 `discover`/`plan`，但所有写入 action 必须失败关闭；bootstrap 不自动安装 AUR helper、不猜测包名、不把独立或 fork 组件强行改走包管理器。
- Stage 0 的 `latest` 只表示 Arch 官方同步源的当前候选版本，不写入 `component-versions.json`；Stage 1 继续使用唯一静态 catalog 做固定版本和漂移治理。
- Bootstrap action 必须标注 `system-installation` 或 `project-initialize`；系统安装不隐式初始化项目，Trellis、CodeGraph、AOE 初始化必须绑定明确 project root 并单独确认。
- seed 与 installation 分别从受版本控制的 `templates/config.toml.seed`、`auth.json.seed`、`config.toml.install`、`AGENTS.md.install` 物化；模板缺失或目标漂移时失败关闭。

## Acceptance Criteria

- [x] source checkout 只发现 `pennix-workflow-bootstrap` 为部署入口，旧 setup Skill 不再出现在 installer collection 中。
- [x] 唯一版本 catalog 驱动所有部署/校验路径，仓库内不存在重复的组件目标版本描述。
- [x] 迁移后的 adapter 测试继续覆盖原子替换、submodule pin、linked worktree、Hook state 保留和失败关闭；FastCtx 由 catalog 的 npm action 与静态模板覆盖，不保留 guidance marker adapter。
- [x] `discover`/`plan` 为只读且不暴露敏感值；未显式确认的 apply 拒绝执行；verify/rollback 只处理本次 receipt 和 hash 匹配的变更。
- [x] 宿主识别区分 native Arch、Arch-on-WSL2 和不支持环境；官方/AUR 安装器选择可验证，缺少 helper 或非目标宿主时写 action 失败关闭。
- [x] 全新环境可独立运行 Stage 0 seed：无 Codex 时完成官方安装、最小 provider 配置、提问 feature 启用、0600 secret materialization 和下一阶段提示词输出；已有配置时失败关闭且不覆盖。
- [x] README 明确给出 seed 脚本和相邻模板目录的可复制运行位置；zsh/bash 直接执行均可用。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
