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

## 重启后运行验收

上述待办已完成。最终 Pennix 源提交为 `230844e33217fb0599e4359dca21a5e109acf938`，CI run `38587191602` 的 `verify` 成功；catalog 已将 FastCtx 固定为 `0.2.29`。完整 15 项 Skill 集合按该精确提交经原生 staging/replace-staged 物化，安装副本与源文件逐字节核对通过；组件生命周期核验为 `match`、无 failures/advisories。

2026-10-14 重启当前 Codex 会话后，实际当前 FastCtx 进程为 `/home/penn/.fastctx/bin/fastctx 0.2.29`。当前会话直接调用 `grep`、`glob`、批量读取和精确分页均通过；容量/分页回执沿准确 `offset` 在当前工作链继续到 `Complete`。FastCtx 新进程探针确认同一连接并发大响应、三页连续分页、批量读取、规范字段和参数误用诊断均通过，错误命令未执行。该行为证据由 FastCtx owner 负责，Pennix 只记录路由合同与实际落点，不将文案测试冒充服务端实现验证。

FastCtx 与 Pennix 生命周期 verify 均为 `status=match`；用户级 `AGENTS.md` 摘要保持不变。FastCtx doctor 对 model-side tool surface 的 INFO 仍如实保留；重启后的当前会话直接 MCP 调用证明本入口可用，但不扩张为不可观测的模型侧全量断言。
