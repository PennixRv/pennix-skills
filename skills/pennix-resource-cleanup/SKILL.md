---
name: pennix-resource-cleanup
description: 用户要求盘点、预览或清理 Pennix 工作流组件产生的缓存、历史输出、Teamwork 或备份时使用；按资源 owner 的原生清理入口执行，默认只读，不做全局垃圾回收。
---

# 工作流资源清理

本 Skill 只负责把“需要清理什么、由谁拥有、如何先预览再执行”收敛到正确入口。资源的目录、状态、保留策略和删除动作仍归产生资源的组件；本 Skill 不接管任何组件的生命周期。

## 固定流程

先读取 [资源策略与结果合同](references/resource-policies.md)，定位当前组件的分类、保留边界和原生入口；这里只提供维护基线，实际配置和能力仍以 owner 当前回执为准。

1. 先列出目标资源、所属组件、当前状态、保留规则和可释放量。读取相关组件的原生状态，不凭路径、前缀、mtime 或目录大小猜测归属。
2. 生成精确的 dry-run 清单，说明每个候选、原因、保留项、阻断项和预计释放量。遇到无法解析、正在写入、活动进程、未知 owner、损坏状态或并发锁时停止并保留原始证据。
3. 删除、淘汰或卸载前确认当前请求已有明确执行授权；尚无授权时再请求批准。用户只批准盘点或预览时停在预览；批准某一组件不扩展到其他组件。
4. 授权后只调用 owner 的原生清理入口，回读实际结果并记录成功、跳过、失败、阻断和释放量。失败按原始回执报告，不改写成“已清理”。

## 入口归属

- Trellis Teamwork：先读取当前 `trellis teamwork --help` 与项目 Skill，由当前原生资源入口核验活动 session、assignment、进程及报告保留要求；不调用已退役的 channel 命令，不猜造 prune 子命令或自行删除运行目录。
- Trellis 任务运行资产：使用当前项目 `task.py runtime` 默认预览，再按对应 digest 确认已获批对象；固定同步锚点、有效 Task/continuity/ownership、恢复记录及未知字段保留。任务 complete/cancel 不授予删除历史权限；终态 delegate-inspect 是历史只读，不重开任务。
- 正式交接历史：使用 `pennix-session-handoff` 的 inspect/read/retention；先核验完整字节、历史和当前依赖，再分别预览 archive 与 purge。ID 加新 digest 才变更，archive 只建立无损 ZIP，不自动退出源。旧 lifecycle/ownership 归此 owner 按 ID 保真迁移，不能让 Task runtime 跨 owner 删除；缺失旧 prompt 或旧 schema 不等于整包垃圾，restore/reopen 不恢复接管权限。
- Trellis 资产备份：使用 `trellis backup list` 盘点，`inspect`／`verify` 分别核验选定完整快照；`trellis backup prune --keep 3` 默认预览，已有明确授权后再带 `--yes`。日常至少保留三个完整快照，不自动 TTL。用户明确要求全部移除时使用 `--all`；包括已确认归属的旧更新快照和受管迁移单文件备份时再带 `--include-legacy`。执行前重新核对预览与实际状态，报告成功、保留、失败、文件数和字节；未知、损坏、不完整和未解决恢复对象分别报告并保护，不能按名称强删。备份内容与源任务、会话及 ablation 恢复事务是不同对象。
- Grok Search 输出：使用 owner 的 `grok-search prune`；默认预览，确认后才带 `--yes`。遵守 TTL、总字节数、文件数和活动写入保护。
- Context Mode：使用 `ctx_purge` 明确声明当前工具支持的 session/source/project 精确范围；普通卸载保留数据。复用 owner 当前版本的空闲维护、内容预算和活动保护，不从旧任务推定统一保留期限，不直接删数据库或目录。
- 其他服务、Docker、系统包管理器、思源笔记、Hikari、NAS 或远程主机：只有在该 owner 已提供并被当前任务允许的原生清理入口时才继续；否则只报告证据门，不猜测或代为删除。
- `pennix-skills`、`pennix-skills-extra` 及其他工作流组件的安装集合：使用 `pennix status|check|uninstall`。未知目录、漂移集合和无法证明 owner 的内容不授予删除权限，其他集合仍遵守自身入口。

## 禁止事项

- 不执行全局 `rm`、按名称前缀批量删除、直接 SQL 删除、跨 owner 删除、远程 SSH 删除或手改缓存、收据、数据库、日志和运行态。
- 不把一次组件清理授权解释为所有组件清理授权，不把 dry-run 结果解释为实际删除结果。
- 不为补齐统计而读取不必要的原始大文件；能由 owner 返回的计数和字节数优先使用 owner 返回值。
- 任务存在时，把核验后的清理结果写入当前任务已有的研究、验收或实现进度落点；不另建重复总台账。清理 Skill 本身不改变任务状态、Git、组件版本或项目资产。

跨组件或 owner 不清时先使用 `$pennix-workflow-routing`；涉及系统组件安装、升级或集合接纳时使用 `$pennix-component-lifecycle`。已核验事实保存到当前任务阶段产物、research 或 execution 自然落点，保留资源 owner、原生命令与回执，不依赖额外研究留存入口。
