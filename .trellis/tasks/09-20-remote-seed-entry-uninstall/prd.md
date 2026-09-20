# 修复远程 Seed 的首会话入口与基础卸载

## Goal

让全新 Arch 主机上的远程 seed 在不猜测 Pennix 来源的前提下，引导下一会话安装唯一的 lifecycle bridge；并决定是否提供只反转 Stage 0 自有资产的显式卸载入口。

## Requirements

- R1: seed 完成信息必须提供可直接粘贴的、唯一且公开的 bridge 安装请求：`PennixRv/pennix-skills`、`skills/pennix-workflow-lifecycle`，并明确本 turn 只安装 bridge，不能假定刚安装的 Skill 已可使用。
- R2: lifecycle bridge 的文档必须说明下一 turn 的确定步骤：显式创建干净 source checkout、以该 checkout 安装完整 collection、再 `discover` 并进入 component-scoped lifecycle。
- R3: 不允许 seed 自动 clone、下载或执行完整 Pennix source；bridge 的安装仍经 Codex 内置 `$skill-installer`。
- R4: seed 不提供 `--uninstall`；完整 workflow 的 component uninstall 必须继续由 `pennix-workflow-lifecycle` 逐 component 处理。
- R5: 文档必须明确 seed 不删除 full collection、`AGENTS.md`、插件、项目资产、`openai-codex-bin`、`auth.json`、`yay` 或 build dependencies；反向操作先完成 bridge 和 collection 安装，再使用 lifecycle 的原生 owner 路径。
- R6: README、Skill 文档、seed 测试和行为契约一致。

## Acceptance Criteria

- [ ] AC1: seed 输出不再使用无来源的“安装 Pennix Skills”指令，并准确表达至少一个 turn 的 bridge 安装边界。
- [ ] AC2: 新会话可按输出通过 `$skill-installer` 获得 `pennix-workflow-lifecycle`，不需要猜测仓库或路径。
- [ ] AC3: bridge 文档给出全 collection 的 clean-checkout 与 `discover` 路径，不声称会自动创建 checkout。
- [ ] AC4: 文档和 seed 输出明确完整卸载仅由 lifecycle 逐 component 处理，且 seed 本身没有未声明的反向删除行为。
- [ ] AC5: `bash -n`、seed 与 lifecycle Python 测试、collection source check 通过。
- [ ] AC6: 完整 collection 安装只迁移与 source 完全一致的 standalone bridge；漂移 bridge 保留并阻断，且不产生重复的同名 Skill。

## Confirmed Facts

- `seed-arch.sh` 当前只输出“请先安装 Pennix Skills”，没有仓库、Skill 路径、source checkout 或重启边界，无法可靠启动首会话 bridge。
- Codex 的系统 `$skill-installer` 需要明确 `--repo` 和 `--path`；安装后 lifecycle Skill 最早在下一 turn 可用。
- 完整 collection 安装器要求干净的本地 `pennix-skills` Git checkout，且不会自行创建 checkout。
- 当前 lifecycle 已有逐组件 `uninstall`：`codex-cli` 由 AUR owner 卸载；`codex-config` 只退回 seed baseline；完整 Pennix Skills collection 只在 exact collection 时移除。
- Stage 0 当前仅写入 `CODEX_HOME/config.toml`、`CODEX_HOME/auth.json`，并安装 `openai-codex-bin`。`yay`、`base-devel` 与 `git` 不能安全归为 Stage 0 专有资产，不能由反向流程自动删除。

## Sealed Decision

- D1: 不增加 `seed-arch.sh --uninstall`。完整 lifecycle 已按 owner 安全卸载组件；重复实现 Stage 0 反向删除既不能证明 `yay`、构建依赖和凭据所有权，也会让 seed 失去最小、一次性入口的边界。
- D2: 使用 Codex `$skill-installer` 安装 bridge 后，完整 collection 的默认发现路径会出现同名 Skill。collection installer 在 source 与 standalone bridge（忽略 Python cache）逐文件一致时删除后者；否则拒绝写入，避免静默删除用户修改或留下不可判定的重复路由。

## Notes

- 修改目标：独立 `pennix-skills` 源仓库。根项目只保留任务事实，不承载组件源码修改。
