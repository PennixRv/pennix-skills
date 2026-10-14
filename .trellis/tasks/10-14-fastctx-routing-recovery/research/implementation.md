# 路由修复实施与交付证据

执行日期：2026-10-14。本记录承接任务已批准的封口 revision 1；规划正文中的 planning 表述是封口时事实，实际状态以原生 task.json 的 approved revision 和 in_progress 为准。

## 修复与归因

共享输出池与 Guarded 固定预算属于 FastCtx owner：修复提交 `a5c56f7` 已推送，最终发布版本目标为 `0.2.29`。Pennix 原路由说明又把容量回执解释为必须等待下一用户轮次，使可恢复结果停住；本任务删除这个约束，在当前工作链按精确 offset/files/after_seq 继续，保留命令副作用保护和协议排除。

参数失败没有发现 0.2.24 与 0.2.26 的规范 schema 漂移。实际调用混用了另一工具的 `run.max_output_tokens`，以及单文件顶层 `path`、批量条目 `file_path`、grep 的 `query`。本任务增加规范字段与错误归属说明；不增加别名或静默执行重试。FastCtx 在 rmcp 解析边界提供对应诊断。

## 已验证

- 路由合同测试 6/6 通过，差异空白检查通过。
- FastCtx fmt、clippy 和全量 cargo test 通过；来源仓库保存其测试证据。
- 根侧离线集成检查 8 项 passed，failed/blocked 为 0。

## 待交付

FastCtx 五平台和七个 npm 包发布验收成功后，更新 lifecycle catalog 固定版本，提交并推送本仓库，按系统安装器暂存与生命周期 replace-staged 更新完整集合，再核对安装副本、收据和实际新 MCP 连接。
