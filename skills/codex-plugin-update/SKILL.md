---
name: codex-plugin-update
description: Prepare, refresh, install, and recover updates for Codex Plugins that provide Hooks, including Git marketplace ownership and actual Plugin MCP process cwd verification. Use when a user asks to install, upgrade, reinstall, or refresh a Codex Plugin with hooks, or when a Plugin marketplace update may replace a versioned Hook/MCP cache. This skill applies only to the Linux/WSL Codex CLI workflow and uses the installed codex-plugin-update/scripts/plugin-update-transaction.py.
---

# Codex Plugin 受控更新

## 适用边界

这个 Skill 处理 Codex Plugin 的更新时序，不修改 Plugin 缓存实现，也不承诺宿主支持
活动会话热重载。含 Hook 的 Plugin 更新必须跨越“准备、旧会话最后一次安装调用、完整退出
并重启 Codex 宿主进程、新进程恢复”四个边界；不含 Hook 的普通 Plugin 更新也应先确认
没有活动 Hook 依赖。只新建、切换或恢复对话不会刷新宿主已经加载的 Hook 绝对路径，不能
代替进程重启。

事务工具的稳定路径是：

```text
${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py
```

工具只把不含秘密的摘要写入：

```text
${CODEX_HOME:-$HOME/.codex}/.local-backup/plugin-update-transactions/<id>/transaction.json
```

该目录属于本地运行状态，必须保持 Git 忽略。事务记录版本、marketplace 来源/revision、
Hook 路径摘要、MCP 目录关系、当前任务和 Git 摘要，不记录配置正文、MCP 环境、
凭据、数据库、日志、完整命令行或会话内容。

## 工作流

### 1. 准备

在真正安装前核对目标 Plugin 的精确 marketplace selector、目标版本和目标 Hook hash。
先完成来源、tag、发布包、固定 ref 和 Hook trust 审查，把精确目标 hash 固定在事务记录中。
不得在事务前单独执行
`codex plugin marketplace upgrade`；事务识别精确来源，Git marketplace 在 `install`
内部刷新，`local` 和内置来源不刷新。
准备事务时 `/home/penn/.codex` Git 工作区必须 clean。项目工作区可以包含在途改动，但事务会固定其
完整 Git 状态摘要，直到 install/recover 都不得发生任何变化；当前项目仍必须有 Trellis 任务。目标 hash 与旧 hash 不同时，新探针可能把旧 Hook 报为
`untrusted`；事务会记录该状态，安装后仍强制目标 Hook 全部 `trusted`。

如果当前 Plugin 的 MCP 已经运行在 `plugin-backup-* (deleted)`，`prepare` 可以记录一个
`mcp.status=degraded`、`degraded_reason=deleted_cwd` 的重建基线。这只适用于这个精确的
已删除工作目录错误；它不是验收通过，也不允许放宽其他 MCP 路径、版本或进程唯一性检查。
此时仍必须执行 `install`、完整重启和 `recover`，只有恢复后的 `mcp.status=verified` 才能
继续工作。

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py" \
  prepare \
  --plugin '<plugin>@<marketplace>' \
  --target-version '<version>' \
  --project-root "$PWD"
```

保存工具返回的 `transaction_id`。准备失败时不得手工绕过检查、删除事务状态或直接执行
安装器；先处理报告的 Git、任务、来源或版本问题。

### 2. 旧会话最后调用

准备成功后，只在同一个 Codex 会话执行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py" \
  install --transaction '<transaction-id>'
```

工具对 Git 来源先执行
`codex plugin marketplace upgrade <marketplace> --json`，重新核验来源身份和 revision，
再执行 `codex plugin add <plugin>@<marketplace> --json`；两步属于同一次终止事务。
`local`/内置来源跳过刷新。成功返回 `action_required=restart_codex_now` 后，当前会话不得再调用
任何工具、修改文件、提交 Git、查询 `status` 或尝试回滚；直接告知用户完整退出当前
Codex CLI/TUI 宿主进程并重新启动。只创建新对话或在线程内恢复会话不满足该要求。
安装命令非零退出也可能已经部分替换缓存，同样必须立即停止并完整重启宿主进程。不要使用
`--dangerously-bypass-hook-trust`，不要把配置文件临时移走作为常规流程，也不要在同一
会话中做后续检查。

刷新、安装或静态核验失败时，事务会保留 `refresh_failed`、`install_failed` 或
`recovery_required`，不要
删除其目录。新会话会区分目标版本已经落地、旧版本完整保留的 `failed_safe` 和未知中间态；
`failed_safe` 只能在修复安装原因后创建新事务，不能当作目标版本安装成功。

### 3. 新进程恢复

完整退出并重新启动 Codex 宿主进程后，必须先运行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py" \
  recover --transaction '<transaction-id>' --project-root "$PWD"
```

恢复命令在 Linux/WSL 中使用 Codex 宿主进程 PID、内核启动标识和启动时间证明安装后已经
重启；恢复同一对话时 `CODEX_THREAD_ID` 可以保持不变，不能把线程标识误当成进程会话标识。
工具同时核对目标版本、marketplace revision、Hook 文件、app-server 实际加载/启用/trust
状态、Trellis 当前任务和两份 Git 摘要。
Plugin 提供 MCP 时，还会对照 `.codex-plugin/mcp.json`、`codex mcp list --json` 和当前 Codex
后代进程的 `/proc/<pid>/cwd`/`exe`。默认目录不存在、已删除、位于 `plugin-backup-*`、不是目标
版本或进程不唯一都会保持 `recovery_required`。唯一的受限兼容态是：重启后的当前 Codex 后代中
唯一 MCP 进程精确匹配 `<marketplace>/plugin-backup-*/<plugin>/<target-version> (deleted)`，命令、
manifest、inventory、稳定 cache、Hook trust、来源和静态环境同时通过。该状态只记录归一化的
`current_release_deleted_backup`，不把随机 backup 名写入事务；错误版本、其他父目录或普通 deleted
cwd 继续失败关闭。工具不读取 `/proc/<pid>/environ` 或完整命令行。成功后才可继续原任务。恢复失败
会保留 `recovery_required` 和不含秘密的错误列表；不得凭记忆宣称更新完成。

若事务工具自身阻断真实恢复，只允许先提交对事务工具、对应测试和本 Skill 的修复。恢复时
仅接受从事务固定提交向后推进的 Git 后代，且提交差异必须完全落在上述受控文件；项目仓库、
任务、Plugin、Hook 或其他用户级文件发生变化仍失败关闭。

### 4. 查询或放弃

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py" \
  status --transaction '<transaction-id>'
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py" \
  abort --transaction '<transaction-id>'
```

`status` 只读。`abort` 只允许原会话在尚未安装的 `prepared` 事务中使用，并且仍会核对
当前 Plugin 版本；已进入安装或重启状态的事务不能通过删除文件来“取消”。

### 5. 历史快照漂移后的安全终结

如果完整重启后 `recover` 发现目标版本已经安装，但项目 Git、`CODEX_HOME` Git、当前
Trellis 任务已因后续工作自然变化，事务会保持 `recovery_required`。只有确认
当前安装仍然可信且不需要回放旧快照时，才允许使用显式的
安全终结命令：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/scripts/plugin-update-transaction.py" \
  finalize-recovery \
  --transaction '<transaction-id>' \
  --project-root "$PWD" \
  --confirm-historical-drift
```

该命令要求新 Codex 宿主进程证明，并重新核验目标 Plugin 版本、marketplace 来源和 revision、
Hook 文件及信任状态、MCP 实际进程 cwd/exe。MCP 仅可处于稳定 cache，或
满足上一节的当前 release 临时 backup 兼容态；后者不表示宿主目录生命周期已经稳定。它只接受上述四类历史
快照漂移；目标未安装、Hook/MCP 不可信、来源变化、活动事务、未知状态或没有新进程证明时
仍失败关闭。成功结果是带有原始失败记录、漂移类别、当前安装摘要和剩余风险的
`failed_safe`，不是把历史快照伪造为仍然有效，也不是删除事务目录。终结后旧事务不再阻断
无关 `prepare`，未来更新必须创建新事务。

## 强制约束

- 该 Skill 是时序和恢复入口，不是 Plugin 发布验收的替代品；先核对来源、版本、校验和、
  安装结果及真实工作流入口。
- 不在事务外执行 `codex plugin marketplace upgrade`。marketplace/ref 的静态目标先固定；
  Git 来源的精确刷新由事务显式建模，来源类型或 CLI JSON shape 漂移时失败关闭。
- 不把 `.local-backup` 中的事务 JSON、Plugin cache、config.toml、auth.json、日志、
  数据库或会话文件加入 Git。
- 事务只允许当前项目的主会话执行。Trellis channel 工作节点不得更新 Plugin、控制事务
  生命周期或代替主会话执行恢复。
- 事务过期、目标版本不符、项目或 `/home/penn/.codex` Git 漂移、任务漂移、缺少 Hook，或除
  `prepare` 重建基线外无法唯一证明 Plugin MCP 进程时必须失败关闭。
- 当前支持范围是 Linux/WSL Codex CLI；Windows、IDE 和桌面应用不在本 Skill 的保证范围。

## 验证

维护或修改事务工具后运行：

```bash
python3 -m unittest discover -s "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update/tests" \
  -p 'test_plugin_update_transaction.py' -v
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  "${CODEX_HOME:-$HOME/.codex}/skills/codex-plugin-update"
```

真实更新前还必须在安装前后复核任务、Git、marketplace 和实际 Plugin/Hook/MCP；没有明确目标版本时只运行隔离测试，不执行真实安装。
