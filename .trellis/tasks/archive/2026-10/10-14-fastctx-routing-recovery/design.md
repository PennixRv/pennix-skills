# 设计方案

状态：planning。仅规划 Pennix 源侧的路由 Skill、合同测试和发布物化；FastCtx 服务端行为属于 `/home/penn/devel/fastctx` owner 任务。根任务和 FastCtx owner 任务的当前决定是本设计的前置事实，不等同实施批准。

## 修改边界

实际修改目标为 `skills/pennix-fastctx-routing/SKILL.md` 及其 `tests/test_contract.py`，必要时更新同一 Skill 的来源/版本记录。保留以下已有边界：

- Trellis 任务、正式交接、原生交互、Hook/MCP/TUI、外部检索、CodeGraph、组件部署和语义编辑继续走各自原生入口。
- 普通本地读取、搜索、非交互命令和后台任务使用 FastCtx；FastCtx 已有工具 schema 时不再包 shell。
- 当前宿主工具域的可用性不能从 `functions.exec` 的 `ALL_TOOLS` 推断；实际错误仍保留为 schema、权限、传输、服务、容量或命令错误。
- Partial 只按响应给出的精确 offset/files/cursor 续读；`run` 已执行后不盲目重跑副作用。

## 本轮合同修正

路由 Skill 只表达可执行的恢复合同：

1. 容量保护和宿主展示截断不是工具缺失，也不结束当前工作；在安全的只读分页场景中按准确参数继续或收窄请求。
2. Skill 不再使用“下一轮调用，不在同轮反复重试”作为容量的正向规则。它应要求避免无界忙循环，并根据 FastCtx 返回的实际 Complete/Partial、错误类别和恢复参数推进。
3. `run`、`run_background`、`job_kill`、`replace` 等有副作用或状态改变的操作不得因为容量提示自动重跑。需要完整命令输出时沿现有重定向或后台日志路径读取。
4. 规范字段是唯一权威。Skill 直接列出高频接口的准确字段：单文件顶层 `file_path`，批量条目 `path`，grep 必填 `pattern`，run 使用 `command/cwd/timeout_ms/login_shell/encoding`；不声明别名，不让模型猜测。
5. 参数反序列化错误应回到调用来源修正。Skill 可以提供字段纠正说明，但不能在调用时自动变换未知字段、静默丢弃 `max_output_tokens` 或模拟另一个工具。

## 误用根因核验

当前已核验的错误调用来自工具域字段混用：`run.max_output_tokens`、单文件顶层 `path`、批量条目 `file_path`、`grep` 缺失 `pattern` 以及把 `query` 传给 `grep`。0.2.24 与 0.2.26 发布的工具 schema 规范化摘要一致，因此没有“近期 FastCtx schema 改名”的证据。

实施前须再核对：

- 实际宿主当前暴露的 FastCtx 工具描述和 `tools/list` 参数；
- Pennix Skill 与模型说明是否把其他工具字段投射到 FastCtx；
- 发生错误的调用域及调用前的参数构造；
- 源 Skill 与安装副本是否同源；
- 测试是否只检查文字而没有验证规范调用。

如果根因落在 FastCtx schema 或宿主生成器，记录 owner 并回根任务/ FastCtx 任务，不在 Pennix Skill 中增加兼容代码。

## 受影响资产

| 资产 | owner | 处理 |
| --- | --- | --- |
| `skills/pennix-fastctx-routing/SKILL.md` | Pennix | 修正容量恢复和规范参数说明，删除误导性下一轮限制 |
| `skills/pennix-fastctx-routing/tests/test_contract.py` | Pennix | 删除“禁止同轮续读”正向断言，增加规范字段和错误类别的静态合同；行为继续由 FastCtx owner 验证 |
| FastCtx `model_guidance.rs`/工具 schema/服务端实现 | FastCtx | 由 FastCtx owner 任务修改，Pennix 不复制或代改 |
| 安装副本 | 系统 lifecycle | 发布后通过 staging/replace 物化，源仓库不直接编辑 |
| 根任务 | 根协调仓库 | 保存 owner 引用、提交、版本和组合验收，不复制 Skill 或 FastCtx 源码 |

## 不纳入范围

不增加参数兼容层、通用路由器、自动重试调度器、统一错误转换器、永久结果缓存、全局 AGENTS 规则或新 FastCtx 配置键。不修改 FastCtx 源码、Codex 二进制、用户配置、凭据、运行进程和其他检索 Skill。

## 验证

除现有 Python 合同测试外，按 FastCtx owner 完成后使用实际新工具清单进行有限行为验证：同一连接连续 read/grep/glob 分页、规范参数直接调用、错误字段拒绝、已执行 run 不重跑、协议排除和宿主工具域判断。Pennix 测试不能单独证明 FastCtx 容量修复。
