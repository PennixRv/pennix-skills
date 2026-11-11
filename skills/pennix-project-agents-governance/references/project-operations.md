# 项目初始化、重入与退出的编排合同

明确授权的项目初始化、重初始化、刷新或移除使用本合同。主 Agent 执行 inspect → plan → native apply/delegate → verify，逐步回读原生结果；这是 N1 的 Agent 编排方法，不提供无人值守执行、统一机器退出码、崩溃自动续跑或另一套状态机。仅审查默认只读，当前任务已有的范围一致授权继续有效。

## 有界 owner 分类及证据

下表来自 2026-11-11 对已登记组件、当时根项目组件源码和现有生成块的核验，只是调用前的核对起点，不是运行 registry 或机器上任意插件的完整发现结果。源码路径相对于各组件维护仓库；执行前核对实际安装版本的原生 help、实现和来源，源码候选不证明已安装或已加载。

| 对象 | 分类与内容边界 | 可核验证据及处理 |
| --- | --- | --- |
| Trellis | 直接项目 writer；TRELLIS 块及其登记资产 | `packages/cli/src/commands/init.ts:createRootFiles`、`packages/cli/src/commands/update.ts`、`packages/cli/src/commands/uninstall.ts`、`packages/cli/src/utils/uninstall-scrubbers.ts`、`packages/cli/src/utils/asset-backup.ts`；初始化、更新、移除、恢复均归 native |
| CodeGraph | local install/uninstall 为直接项目 writer；CODEGRAPH 块与目标宿主配置 | `src/installer/targets/codex.ts`、`src/installer/targets/shared.ts:upsertInstructionsEntry/removeProjectInstructionsEntry`、`src/bin/codegraph.ts`；Codex/OpenCode 可能共享项目 AGENTS，不能只退出一个消费者就假定可删块 |
| Pennix Lifecycle 的 codex-agents | 用户层 writer；不属于项目 writer | catalog 的 codex-agents 目标为 `codex_home / AGENTS.md`，`project_init=not-applicable`；系统物化不能授权改项目指令 |
| CodeGraph global 操作 | 全局配置 writer；当前 Codex/OpenCode 路径保留用户 AGENTS | `src/installer/targets/codex.ts` 等 target 的 location 分支；不得将 global 与 local 混用 |
| Context Mode | 指令消费者／宿主配置 owner；不是项目 AGENTS writer | `src/setup/registry.ts:assertWritable` 禁写 AGENTS、AGENTS.override 等指令文件；遵循原生 setup 边界 |
| Pennix Skills | 治理方法与只读 inspector；人工正文按授权编辑 | `pennix-project-agents-governance/scripts/inspect_chain.py`、本 Skill 及项目资产诊断；生成块委托原生 owner，不成为第二 writer |
| extra、Windsurf、Tavily、Grok、Paseo relay／translation、cch-status | 有界源码检索未发现直接项目 writer | 当时根组件字面检索仅为初筛，不能排除动态调用、依赖或外部插件；新动作须追到真实调用方 |
| Agent of Empires | 可选项目入口，尚未证明为 AGENTS writer | catalog 为 project-only；当时原生 help 的 init 对象为 `.agent-of-empires/config.toml`；先查 hooks／启动链，不据组件可用就选入 |
| GitNexus、未知标记或项目脚本 | 项目特定／未知 writer | 现有 gitnexus 块只能证明内容存在；查初始化器、Hook、package lifecycle 和源模板。保留未知内容，不自动安装、索引、迁移或认领 |

新增组件只有具备真实写入调用、路径、作用域、内容 owner、原生重入／移除入口和验证证据后，才纳入本次选定动作。未知归属阻断可能触及它的动作；能证明不受影响的已授权步骤可继续，不能把“没搜到”改报为“不存在”。

## inspect 与 plan：固定目标和原生范围

1. 固定真实绝对项目根、当前 checkout/submodule、cwd、宿主和选定的组件／动作。不要穿越独立仓库，也不要把用户 HOME 或 CODEX_HOME 当作项目根。区分全新、已有管理资产、部分完成和纯审查。
2. 读取适用指令、已有文件与来源链，识别手工正文、T/C/未知块及其 owner。检查 marker 缺半、倒序、重复、可识别的跨 owner 嵌套、非普通文件、符号链接和不安全路径；未知或异常先停受影响写操作。按[来源链](codex-chain.md)核对 override/fallback、预算和遮蔽，inspector 保持 `host_loaded=false`。
3. 核对实际 native CLI 身份、版本和 help，列出本次精确命令、预期路径、变化区域、后置条件、未选组件与停止条件。系统能力缺失转[Lifecycle](../../pennix-component-lifecycle/SKILL.md)，不自动部署；系统组件部署、集合物化与项目接入是不同动作。
4. 记录必要的当前内容和原生预览以比较块外字节、配置及外部变化；只在现有 task/Issue 留必要证据，不保存凭据、运行态或整份私有配置。不手改原生摘要、manifest 或安装记录。

## native apply/delegate：串行操作与顺序兼容

通常先 Trellis 后 CodeGraph，每步验证后再执行下一步。若现场先有 CodeGraph，Trellis 也必须保留 C 和正文；两种顺序都是合同内的兼容场景，不能以推荐顺序掩盖 writer 缺陷。只选一个 owner 时不安装另一个。

| 动作 | 原生入口与范围 | 后置条件及限制 |
| --- | --- | --- |
| Trellis 首次接入／明确重初始化 | 明确项目根与已选平台后按实际 `trellis init --help` 调用 | 目标 N2 行为：无 AGENTS 时创建；已有正文且无 T 时普通初始化（含 `--yes`）严格预检后安全追加 T；已有合法 T 普通初始化保留，重复不重复块；显式 `--skip-existing` 保留并报告缺块未接入 |
| Trellis 更新／工作流刷新 | [项目更新 Skill](../../pennix-trellis-project-update/SKILL.md)的 `trellis update --dry-run`、候选和选定 workflow 原生入口 | 不把已有项目更新替换为全套 init。T force 仅替换 T，保留正文与其他 owner；其他资产仍遵循原生覆盖合同，整次 init force 可能覆盖 `.codex/config.toml` 等文件，不能为补一个缺块使用它 |
| CodeGraph Codex local 接入／受限重入 | 在明确项目根执行 `codegraph install --target codex --location local --yes` | 核对 `.codex/config.toml` 中本 owner MCP 配置和唯一 CODEGRAPH 块，保留其他配置。需要 worktree 绑定时按原生能力及已授权合同加参数；此命令不含 `--init`，索引需单独明确授权 |
| CodeGraph 仅刷新已选 Codex local | 使用上一行普通 install 重入 | 当前 `install --refresh` 遍历 ALL_TARGETS，忽略 `--target` 对 sweep 的限制；`--location local` 只能缩小 location。仅 `--yes` 默认 global/auto，不能代表受限修复。upgrade 成功而 refresh 警告也不能报项目刷新成功 |
| 移除选定 owner | 查看当前 `trellis uninstall --help` 或 `codegraph uninstall --help`，按实际支持的精确项目／target／location 预览并执行 | 只撤回本 owner 有依据的区间和配置；T 未登记历史块不自动认领。C 有其他已知共享消费者或消费关系未知／不可读时保守 `kept`；报告保留原因，不强删共享块 |
| 恢复或 ablate/restore | 仅在精确授权下使用相应 native review／restore | 备份前无文件、正文无 T、有 T 分别核验；后来出现其他 owner 内容时，不得删除 AGENTS 或回写旧全文。不能证明安全则 conflict 并保留当前内容；独立 ablation 的严格指纹预检不套用宽松块恢复结论 |

N2 是本轮 Trellis writer 的目标合同。调用前必须核对实际交付版本：旧版缺 T 跳过不能报已接入，未具备新行为时报告受限并由原生 owner 处置，不手工补生成块或用整次 force 绕过。AGENTS 块级保护不证明其他共享配置安全合并。

## 部分完成、失败与重入

每步同时核对退出码、原生结果和真实文件。Trellis 可能只写了部分资产；CodeGraph 即使先做路径预检，后续仍可能出现 MCP 已写而 AGENTS 块失败。目录、版本文件或单步退出码 0 都不能代表整体完成。显式 skip、冲突候选待处理、不可核验项分别报告。

失败停止依赖步骤，保留已成功 owner 的结果与可用诊断，不自动反向卸载成功项或还原共享文件。恢复时重新 inspect 现场与外部变化，区分已完成、部分完成、未执行、未选和未核验；从失败 owner 的最小 native 动作重入，重验成功项后再继续。取消和中断采用同一规则，不造自动恢复台账。

Trellis 常规全文件摘要可能保守冲突：T 已是当前模板时，他方追加不必触发变更；T 模板也变且块外被修改时可能进入冲突。保留 native skip、`.new` 候选和明确覆盖审查，不直接重登记 hash。写前核对能发现的陈旧快照或外部变动，发现后停止并重新评估；串行编排、单文件原子替换、原生维护锁和摘要检查均不等于任意外部 writer 互斥、比较交换或全局事务，不能承诺没有丢写窗口。

## verify：最终联合核验

- 对所有已选 owner，检查预期块唯一且合法、配置真实存在及原生状态；未选组件、项目手工正文与其他块保持。对块外字节、换行、尾空格、多空行作差异比较，追加分隔空白按 native 生成边界判断，不承诺未知历史安装可逐字节逆转。
- 隔离组合 fixture 覆盖无文件／正文／T／C／未知块、非 ASCII 和 CRLF、T→C 与 C→T、重复接入、T force、异常 marker／路径拒绝、部分失败重入、摘要冲突、外部变化、两种移除顺序与共享消费者退出、恢复三种前态。真实用户文件不用于破坏性试验；单 owner 测试不能代替组合结果。
- 分层报告文件层成功、来源候选、宿主信任、真实指令加载和 MCP 生效。override 遮蔽、预算截断、项目未受信任或缺宿主加载回执时明确限制；mock 文件和 inspector 均不能证明现场加载。
- 将每步已执行／失败／受限／未运行、保留的成功项、待处理候选和下一重入点写回当前 task/Issue。所选动作的联合后置条件不足时保持未完成，不用版本字符串、已安装工具或干净工作树代替验收。`collection.json` 仍是集合交付的唯一清单。
