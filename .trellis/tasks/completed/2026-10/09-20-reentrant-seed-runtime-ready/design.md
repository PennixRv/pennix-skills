# 技术设计：可重入 Seed 与原生 Skills 安装

## 运行时边界

Seed 只建立可启动的 Codex 基线：Arch 主机检查、官方 `npm`、AUR
`openai-codex-bin`、seed-owned `config.toml` / `auth.json`。它不拥有 Codex agent 内的
`$skill-installer`，因此不伪造该工具、下载源码 checkout 或发布另一套运行时
bundle。

完成 seed 后，一个新 Codex 会话的第一轮使用系统 `$skill-installer` 只在最终 collection
destination 内安装 `pennix-workflow-lifecycle` bootstrap。安装器确认后保持同一会话，下一轮
直接调用该 Skill；bootstrap 在该会话补齐 collection 后继续部署。这是原生 Skill 在下一轮才
可用的边界，不是第二个部署阶段，也不需要第二个会话。

## Seed 重入规则

- 先完成宿主、路径、模板和包冲突检查；已有 `config.toml` / `auth.json` 不是错误。
- `openai-codex` 是 catalog 明确登记的 `openai-codex-bin` replacement，使用已选
  AUR helper 的原生 remove 动作迁移；Seed 不猜测或删除未登记的包所有者。
- `config.toml` 不存在时才读取 `base_url` 并原子写入；`auth.json` 不存在时才
  读取隐藏 API key 并以 `0600` 原子写入。
- 两个文件都已存在时不读取 stdin 或 `/dev/tty`，仍确认 Codex 包并输出首轮
  指令。
- 失败清理只删除本次创建的文件，绝不影响之前已有的配置或凭据。

## Collection 安装合同

`$skill-installer` 的安装 destination 是 `CODEX_HOME/skills/pennix-skills`。
第一轮只安装 lifecycle bootstrap；同一会话的下一轮从 catalog 的
`collection_contract.remaining` 读取全部剩余来源。父仓库 GitHub archive 不包含
submodule 内容，故剩余的 `grok-search` 与 `windsurf-code-search` 必须分别从其拥有仓库
安装到相同 destination。此内部合同不出现在 seed 的用户提示中。

系统安装器不覆盖既有 destination，故下一轮只安装尚未存在的 remaining Skills。
`pennix-skills` 的后续 install/upgrade 不得再由 lifecycle CLI 伪装为可执行的
checkout 管理动作；catalog 将其标记为 native-owner，并将用户路由回 Codex
`$skill-installer`。卸载仍只允许移除精确的、已知 Skill 名称集合或精确 bootstrap。

## Lifecycle 发现

`pennix-skills` 探测从 catalog 的受管 Skill 名称集合验证 destination 的直接
entry set 与每个 `SKILL.md`。只含 lifecycle bootstrap 的精确目录报告为 `bootstrap`；
任意其他不完整形状报告为 `drifted`。它不读取或要求 `--source`，故 `discover` 保持纯
只读且可在目标机运行。`verify` 对完整安装形状进行校验。

## Compatibility

旧的独立 lifecycle bridge 不会由新 seed 创建。新的 bootstrap 直接位于最终 collection
目录，且仅在完全一致时可卸载。此任务不自动删除历史 bridge；它属于旧流程留下的独立资产，
自动删除会越过当前 seed 的所有权边界。用户文档只给出同一会话两轮路径。
