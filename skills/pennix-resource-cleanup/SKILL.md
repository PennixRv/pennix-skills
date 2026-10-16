---
name: pennix-resource-cleanup
description: 用户要求盘点、预览或清理 Pennix 工作流组件产生的缓存、历史输出、Channel 或备份时使用；按资源 owner 的原生清理入口执行，默认只读，不做全局垃圾回收。
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

- Trellis Channel：使用原生 `trellis channel prune`；默认预览，确认后才带 `--yes`。活动 worker、不可读或损坏的 `events.jsonl`、无效 PID 和无法验证的进程身份必须闭锁。
- Trellis update 备份：使用原生 `trellis backup list` 查看，使用 `trellis backup prune --keep 3` 预览，确认后才带 `--yes`。未知或未完成备份阻止整批删除。
- Grok Search 输出：使用 owner 的 `grok-search prune`；默认预览，确认后才带 `--yes`。遵守 TTL、总字节数、文件数和活动写入保护。
- FastCtx 作业历史：使用 FastCtx 自己提供的历史维护或配置入口；不得通过 `run`、普通 shell、`rm` 或直接删除 job 目录代替 owner 操作。运行中作业和待启动 reservation 必须保留。
- 其他服务、Docker、系统包管理器、思源笔记、Hikari、NAS 或远程主机：只有在该 owner 已提供并被当前任务允许的原生清理入口时才继续；否则只报告证据门，不猜测或代为删除。
- `pennix-skills`、`pennix-skills-extra` 及其他工作流组件的安装集合：使用 `$pennix-component-lifecycle`。明确选定的 `pennix-skills` 暂存由其 `discard-staged` 预览并按摘要执行；未知目录的发现不授予丢弃权限，其他集合仍遵守自身入口。

## 禁止事项

- 不执行全局 `rm`、按名称前缀批量删除、直接 SQL 删除、跨 owner 删除、远程 SSH 删除或手改缓存、收据、数据库、日志和运行态。
- 不把一次组件清理授权解释为所有组件清理授权，不把 dry-run 结果解释为实际删除结果。
- 不为补齐统计而读取不必要的原始大文件；能由 owner 返回的计数和字节数优先使用 owner 返回值。
- 任务存在时，把核验后的清理结果写入当前任务已有的研究、验收或实现进度落点；不另建重复总台账。清理 Skill 本身不改变任务状态、Git、组件版本或项目资产。

跨组件或 owner 不清时先使用 `$pennix-workflow-routing`；涉及系统组件安装、升级或集合接纳时使用 `$pennix-component-lifecycle`。需要持久化已核验事实时使用当前项目的 `$trellis-research-record`，并保留资源 owner、原生命令和原始回执。
