# 资源策略与结果合同

此表用于选择负责组件和核验边界；不是并行版本清单，也不证明远程部署已启用某项机制。版本来源使用 lifecycle catalog，保留配置与可执行入口从当前 owner 取得。没有原生预览能力时只做只读盘点，不用 shell 模拟清理。

| 组件 / owner | 对象、可重建性 | 默认保留 / 容量边界 | 原生入口与保护 / 所需证据 |
| --- | --- | --- | --- |
| Grok Search | 完整结果、运行输出；可重新请求但可能有成本 | 30 天、1 GiB、4096 文件；单次维护最多 8192 条目 / 5 秒 | `grok-search prune` 默认预览，授权后 `--yes`；临时文件、符号链接、活动 grace 保护；回执核对候选、失败和实际文件字节 |
| Context Mode | 本地会话派生事件、恢复材料及明确主动索引；原始 Codex 历史归宿主 | 自动会话派生数据按最近活动保留 30 天，当前会话受保护；普通主动索引保留 | `ctx_purge` 要求 `confirm: true` 及 `scope: session/project`；session 仅当前核验线程；无原生预览时只读盘点，普通卸载保留数据；不扫描旧根或其他 owner |
| Trellis Channel | 临时频道与 worker；最小会话关系记录是权威历史 | 原生 age/candidate 选择，不以目录名证明可删 | `trellis channel prune` 默认预览，授权后 `--yes`；事件、PID、身份和 admission 锁未知均保留；频道清理不删除关系历史 |
| Trellis backup | 项目更新恢复快照；不可凭空重建旧定制 | 最近至少 3 个完整备份；无自动 TTL 删除 | `trellis backup list` / `prune --keep 3`；授权后 `--yes`；更新事务、未知与不完整状态整批阻断 |
| Trellis mem / task | 原始对话、任务事实与索引；原始历史不可重建 | 按原生历史/归档合同，不作为通用缓存淘汰 | 使用项目原生归档、索引入口；索引可重建不授权删除源历史 |
| 正式交接 | 交接包、rollout 投影、恢复材料 | 按交接 owner 的 archive/restore/purge 合同 | 使用 `pennix-session-handoff`；归档、恢复和彻底删除语义不同，不直接删目录 |
| AOE | worktree、trash、容器、projection；可能含未提交工作 | trash 默认 30 天，实际 profile 为准 | AOE 原生 purge/restore；先取得 dirty 检测、活动保护、per-profile force 和 projection forget 证据，缺证不删 |
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
