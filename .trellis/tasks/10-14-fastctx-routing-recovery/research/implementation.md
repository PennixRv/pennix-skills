# 路由修复实施与交付证据

执行日期：2026-10-14。本记录承接任务已批准的封口 revision 1；规划正文中的 planning 表述是封口时事实，实际状态以原生 task.json 的 approved revision 和 in_progress 为准。

## 修复与归因

共享输出池与 Guarded 固定预算属于 FastCtx owner：修复提交 `a5c56f7` 已推送，最终发布版本目标为 `0.2.29`。Pennix 原路由说明又把容量回执解释为必须等待下一用户轮次，使可恢复结果停住；本任务删除这个约束，在当前工作链按精确 offset/files/after_seq 继续，保留命令副作用保护和协议排除。

参数失败没有发现 0.2.24 与 0.2.26 的规范 schema 漂移。实际调用混用了另一工具的 `run.max_output_tokens`，以及单文件顶层 `path`、批量条目 `file_path`、grep 的 `query`。本任务增加规范字段与错误归属说明；不增加别名或静默执行重试。FastCtx 在 rmcp 解析边界提供对应诊断。

## 已验证

- 路由合同测试 6/6 通过，差异空白检查通过。
- FastCtx fmt、clippy 和全量 cargo test 通过；来源仓库保存其测试证据。
- 根侧离线集成检查 8 项 passed，failed/blocked 为 0。

## 发行与来源验收

- 路由修复提交 `4651ccd61ef54eef217ea172598c619185373710` 已推送至 main 和当前分支；CI https://github.com/PennixRv/pennix-skills/actions/runs/38582897688 成功。
- FastCtx 最终 `v0.2.29` 指向 `9d655614a326bf543d81697a747bc230259e0c19`。五平台及 publish-release 全部成功：https://github.com/PennixRv/fastctx/actions/runs/38581885462 。
- GitHub Release 的五个归档服务器摘要与 SHA256SUMS 一致；七个 scoped npm 包均由官方 registry 读取到 `0.2.29`。发布后短暂的部分 E404 已消失，没有以 CI 状态代替 registry 验收。
- catalog 的 FastCtx approved_version 已固定为 `0.2.29`；参数段移至独立位置，常规路由步骤继续归入路由规则。

## 安装与最终验收

下一步按系统安装器暂存与生命周期 replace-staged 更新完整集合，核对安装副本与收据；通过原生 package upgrade 和 FastCtx apply 更新稳定入口，再核对新进程、新 MCP 连接和当前宿主生效边界。
