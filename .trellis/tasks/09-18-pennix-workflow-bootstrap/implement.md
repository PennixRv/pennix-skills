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

## 本轮验证记录

- 46 项 bootstrap/adapters 测试通过；包含已有配置或 `auth.json` 拒绝、`openai-codex-bin`
  冲突包在安装前拒绝，以及 zsh 调用 Bash shebang 的回归测试。
- `bash -n`、Python 编译、两个 Skill validator、10 个 Skill collection check、任务 context validate 和 `git diff --check` 通过。
- 当前 WSL2 Arch 的只读 `discover`/`plan` 已核验 package owner、官方候选版本和 applyable 分类；未执行真实安装或写入。
