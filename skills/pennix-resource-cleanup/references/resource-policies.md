# 资源策略与结果合同

此表用于选择负责组件和核验边界；不维护版本清单，也不证明远程部署已启用某项机制。组件来源和动作由独立 `pennix-lifecycle` catalog 声明，实际安装目标查原生锁与回执；集合成员和物化来源查各自 `collection.json`。保留配置与可执行入口从当前 owner 取得。没有原生预览能力时只做只读盘点，不用 shell 模拟清理。

| 组件 / owner | 对象、可重建性 | 默认保留 / 容量边界 | 原生入口与保护 / 所需证据 |
| --- | --- | --- | --- |
| Grok Search | 完整结果、运行输出；可重新请求但可能有成本 | 30 天、1 GiB、4096 文件；单次维护最多 8192 条目 / 5 秒 | `grok-search prune` 默认预览，授权后 `--yes`；临时文件、符号链接、活动 grace 保护；回执核对候选、失败和实际文件字节 |
| Context Mode v2 | 共用项目库中的 journal events、sources 与 chunks；原始 Codex 历史归宿主 | 按上游策略过期所有索引，不为当前 session 或主动索引增加永久保护；默认根 `~/.context-mode` | `ctx_purge` 严格选择一个参数：`session: <id>`、`source: <label/handle>` 或 `project: true`，以当前工具声明为准；project 会影响 Git common directory 对应的共享项目库及其他 worktree。先核验项目、范围并取得删除授权，无原生预览时只读盘点；普通卸载保留数据，v1 旧根只能用经核验的一次性 owner 清理入口 |
| Trellis Teamwork | Session 事件、attempt 报告、worklog、诊断与恢复证据 | 不按统一 TTL 淘汰证据；settled、无 worker 或目录名都不充分 | 先核接受证据、结果引用和恢复义务，再预览 cleanup-artifacts；获批 attempt 处置后再查 rm/prune 的 session 重放职责。rm 默认预览，prune 保留筛选与 --yes，执行均需当前 digest；旧版本不支持该合同则保留。真实 result/evidence/recovery 引用保护，普通盘点提及不自动产生永久保留；kill/reconcile 的合法中断能力独立保留 |
| Trellis backup | 受管资产快照及迁移单文件副本；不可凭空重建旧定制 | 日常保留最近至少 3 个已核验完整快照；无自动 TTL | `trellis backup list`、`inspect`、`verify`、`prune --keep 3` 默认预览；授权后 `--yes`。显式全清用 `prune --all --include-legacy`，只纳入已核实旧 writer 的快照及受管迁移 `.backup`；活动更新／恢复及其回退快照、未知／不完整对象受保护。恢复先预览并核对 `--review`，任务布局及阶段运行时不兼容时拒绝 |
| Trellis mem / task | 原始对话、任务事实、有效控制记录与可退出投影分开 | planning／in_progress／completed／cancelled；completed 按月分层，历史不按缓存淘汰 | complete/cancel 不删除历史。task.py runtime 默认预览已知空业务投影、被替代 marker 和符合协议切换/无引用条件的旧锁；匹配 digest 才执行。保留有效指针/run、未知字段、ownership/continuity、恢复证据与固定锚点；不能完整核验旧锁 waiter 时只保护相应旧锚点 |
| 正式交接 | core、完整历史、prompt、追加 receipt、旧控制证据与恢复材料 | 不按旧 schema、年龄或已终态决定丢弃；全部原始字节保留 | inspect 分开报告存储、历史、当前准入和 Task 观察；逻辑 locator 原生读 plain/ZIP/旧 archive。archive 逐成员 SHA 并保留源，purge 是独立 ID+digest 批准的源退出，ZIP 留存；intent/tombstone 失败按 owner 精确恢复。旧 ownership 仅作历史，restore/reopen 不恢复 authority，不手删 runtime/handoff-* |
| AOE | worktree、trash、容器、projection；可能含未提交工作 | 从当前 profile/原生能力核验；不沿用未证实的统一 30 天假设 | 原生 purge/restore，核对 dirty、活动保护、force 作用域和 projection forget；daemon 不可用按真实失败报告，不为盘点自动启动，缺证保留 |
| Codex / Ponytail Plugin | history、rollout、诊断日志、shell snapshot、插件 Store | 宿主自己的保留与版本机制；用户历史保留 | Codex 原生管理入口；旧 catalog key 持续增长需先有元数据证据，插件静态资产不另建 GC |
| CCH | 派生 snapshot、状态缓存与临时文件 | 已有 owner 限定的年龄/数量维护，当前有效配置为准 | 原生 CCH 状态/维护入口；不读取凭据或原始日志补造统计，已有维护不重复实现 |
| CodeGraph | 项目派生索引、resolver、WAL、daemon | 已有 LRU、失效与 WAL 维护 | 项目明确授权的原生 `uninit` / 重建；可重建索引与项目源码分开，不能用全局 rm 替代 |
| Windsurf Code Search | 一次调用的进程和输出；无共同持久结果缓存 | 已有调用时间、读取与输出预算，退出清理 | 查询入口不授予凭据/config 清理；无持久响应缓存无需添加 LRU |
| Hikari / Tavily / NAS | 服务数据库、爬取结果、日志与缓存 | 客户端机制不能证明 NAS 配置或物理回收 | 先只读取实际部署版本、有效策略、owner、占用和触发入口；逻辑 TTL 不等于数据库/磁盘已释放 |
| SiYuan | 用户知识、历史、资源、派生索引 | 内核策略与用户配置为准；知识不是缓存 | 原生知识/内核接口及明确意图；禁止直接 SQL、资源目录删除或跨 NAS 清理 |
| tmux | 会话、pane 历史与服务进程 | 当前 tmux 选项；会话保留不等于缓存 GC | 原生会话管理，需精确会话授权；不能因无活动客户端就推断会话可删 |
| Pennix lifecycle / 两套 Skill 集合 | 安装树、静态配置与工具自有状态 | 权威安装状态；正常事务清理，不适用 LRU | `pennix status|check|uninstall`；漂移、未知 owner 和外部维护内容保留，不直接删除目录或状态文件 |
| Docker / 系统包管理器 | 镜像、volume、日志、包缓存 | 对应 owner 有效策略；volume 可能含权威数据 | 原生 owner 入口与精确对象授权；先取得部署/日志/磁盘证据，禁止 system-wide prune |

## 计划与结果

每次计划保留：owner、资源类别、精确目标、当前状态、保留策略、候选与原因、保护/未知项、预估量、原生命令、锁/权限、恢复价值和来源。原生工具只能按策略重算候选时，先明确该边界；不要把预览当成冻结的删除集合。

结果使用以下语义，按 owner 回执映射，不伪造组件内部状态：`candidate` 为候选，`eligible` 为 owner 确认可删，`unknown` 为证据不足，`blocked` 为条件阻断，`executed` 为实际成功，`skipped` 为执行时跳过，`failed` 为失败，`retained` 为按策略保留。

分别记录候选/成功/跳过/失败数量、预估和实际释放文件字节。文件大小总和不证明底层文件系统的物理块变化，TTL、压缩、checkpoint、VACUUM、unlink 和归档也不能互相代替；没有该层证据时明确限制。出现部分失败时保留成功与失败明细，遵守 owner 的停止和恢复合同，不自动扩大清理范围。
