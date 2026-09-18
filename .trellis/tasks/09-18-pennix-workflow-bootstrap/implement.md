# 实施与验收计划

## 顺序

1. 创建 `pennix-workflow-bootstrap` Skill 和 `scripts/bootstrap.py`。已完成。
2. 建立唯一 `references/component-versions.json`，清理 setup Skill、README 和 adapter 中重复的
   具体目标版本描述。已完成。
3. 将旧 setup 脚本、测试和 CodeGraph reference 迁移到 `scripts/adapters/` 与 bootstrap `tests/`。已完成。
4. 删除旧 setup Skill 的 `SKILL.md`，避免继续暴露并列部署入口。已完成。
5. 新增 `trellis.py` native adapter；更新 README、AGENTS 和 routing 文档中的路径/名称。已完成。
6. 实现只读 `discover`/`plan` 和受确认保护的 `apply`/`verify`/`rollback` 基础流程；项目可选动作保持明确计划。
7. 运行完整 Python 测试、source collection check、Skill validator 和 bootstrap fixture 自检。已完成。
8. 增加 Arch Linux 宿主探测：区分 native/WSL2、阻断非目标宿主，选择 `pacman` 或已存在的 `yay`/`paru`；补充 fixture 回归。
9. 增加 catalog 约束的上游 inspection：AoE 以 AUR package 作为交付源，上游脚本只提供受限语义证据；
   `upstream-contract-changed` 阻断 action，reviewed digest 绑定到 apply receipt。

## 交互与门禁验收

- `plan` 输出具名 action，原生/文本提问都要求提问即停；未获得下一 turn 的答案不得执行写操作。
- `config.toml` 仅允许 seed/install 模板声明的可移植静态字段；catalog unknown/degraded action 失败关闭。
- 项目动作首次只显示计划；MCP questionnaire 不是默认安装路径。
- 交互回归测试覆盖：原生工具直接调用、禁止使用 `ALL_TOOLS` 判定缺失、schema 错误单次修正、
  宿主拒绝/取消/超时的分类、无答案停点和文本回退。

## 保护条件

- 不执行真实 FastCtx apply、Trellis init/update、CodeGraph init、Hook merge 或项目 workflow 改写。
- 不读出任何 token、凭据、完整用户配置或运行态数据库。
- 不修改 `/home/penn/.codex`；安装副本只在后续明确发布/安装阶段更新。
- 不修改 Trellis、CCH、OpenViking 或 Windsurf Code Search 源码。

## 验收

- 源码只发现 `pennix-workflow-bootstrap` 为部署 Skill，旧 setup Skill 不再被 installer 发现。
- adapter 测试仍覆盖旧脚本的安全不变量：原子替换、symlink/drift 拒绝、linked worktree 拒绝、
  Hook state 保留和 submodule pin 检查。
- `bootstrap.py discover` 不写入文件、不运行 apply、不暴露 secrets；`plan` 输出动作 owner、scope、
  风险和 confirmation；apply 未确认时失败关闭。
- `scripts/adapters/skills_install.py --check` 验证迁移后的 10 个直接 Skill 集合，且安装器不把内部 adapter 目录
  当作独立 Skill。
- 宿主探测 fixture 覆盖 native Arch、Arch-on-WSL2、非 Arch 和未知 WSL；live 环境只确认当前宿主事实，
  不执行包安装或跨宿主动作。
- Stage 0：`bash -n`、bash/zsh 调用、模板缺失/渲染、fake `pacman`/`sudo`/`codex` fixture、
  `config.toml`/`auth.json` 权限和 secret 非泄露检查。
- 上游 inspection：已知控制面、未知环境变量、命令行参数解析变化、inspection 未请求、阻断 plan、apply
  不 inspection 及 digest 缺失均有 focused test；不执行真实远端脚本或 AUR 安装。

## 本轮验证记录

- 65 项 bootstrap/adapters 测试通过；覆盖已有配置或 `auth.json` 拒绝、`openai-codex-bin`
  冲突包、`CODEX_HOME` 与安装目标符号链接、非目录目标、dirty source checkout、npm 命令冲突、
  原生 plugin 半失败的 marketplace 补偿，以及 zsh 调用 Bash shebang。
- `bash -n` 和 Python 编译通过。source collection check 与 `git diff --check` 在 source commit 后重跑，
  因为安装器现在正确拒绝未提交 source。
- 当前 WSL2 Arch 的只读 `discover`/`plan` 已核验 package owner、官方候选版本和失败关闭分类：
  `openai-codex-bin` 阻断官方 Codex action；Trellis 的 npm inventory 与实际命令漂移被阻断；FastCtx
  npm candidate 未发布时被阻断。未执行真实安装或写入。
- `config.toml.seed` 只拥有 provider/auth-store/Default-mode 提问字段；installation fragment 只拥有
  workflow feature policy 与原生 agents 禁用，不接管 model、sandbox/approval、TUI、history、MCP、plugin
  marketplace、hook trust 或主机路径。两阶段模板均拒绝非精确受管状态，重复 apply 为 no-op。
- CCH 和 Tavily Hikari 只作 catalog discovery：CCH 的 endpoint/token-file 与 Hikari 的 endpoint/token
  由各自 native/external owner 管理，缺失时保持 plan-only；OpenViking plugin action 不宣称远端服务已健康。
