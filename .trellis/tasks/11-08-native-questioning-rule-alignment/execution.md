# 实施证据

根完整合同及授权已经生效，本组件按旧版原生规划门禁启动。完成三个 Skill 的局部修改，删除旧强制 Context Mode 语句，区分同步直接工具与嵌套清单、宿主用途限制，以及 Tavily 请求前本地失败与请求后错误。

新增 app-server 采集入口，复用原 runner 的固定来源、归属校验、认证与预算记录；保留 exec 场景。交互、问题答案、异步观察与原生错误有离线测试。根测试 12、eval 13、decision-grill 12、routing 5 均通过，collection 15 Skills/2 commands 与三个 quick_validate 通过。

固定源码提交后由根任务经 Lifecycle 在隔离目录物化；真实协议、模型与实际安装证据仍待补齐，不将上述静态通过报告为行为修复完成。

## 实际协议及模型复核

源码 `3ef9af40b5f93e3b857115686e3175e2bc1a6894` 经 Lifecycle owner 在隔离 CODEX_HOME 物化，collection digest 为 `05f0ac7429628249d957d745fbf1d160a9f589da2a8e631a3eb88f1465d3577b`。真实模型执行 before 两例、after 六例；偏好提问前后均调用 `request_user_input` 并取得答复，未复现历史误报或异步调用，不能声称 before 必败。after 还验证已定事项不重复问、声明路径及引用全文、同线程原生压缩后沿断点继续、请求前回退边界、小全文原生读取和大文件执行器统计。六例均按实际轨迹人工复核；未发检索请求、未读认证或修改 fixture。

初版采集器错误地把 `isBlocking=false` 统计为异步。已按真实 rollout 的 function_call 名称修正，绑定宿主返回的 sessions 路径、线程和 turn，不从 UI 标志推断工具。原始私有 trace、旧 summary 保留，根记录解释更正，不覆盖失败历史。新增回归后 eval 单元 14 项通过。

Codex 0.167.0 原生协议加本地确定性模型 fixture 验证四例：Default 正常答复、空答案、取消，以及 Plan 正常答复。四例均在收到回执前不继续请求模型；取消为 interrupted 且无后续请求，空答案原样返回 `{}`。Default 的 `request_user_input` 对应 `isBlocking=false`，Plan 为 true，均不是 `request_user_input_async`。此层只证明协议，不代替真实模型选择。依据为 OpenAI Codex `rust-v0.167.0` 的 `codex-rs/core/src/tools/handlers/request_user_input.rs`：`is_blocking: mode == ModeKind::Plan` 且 await 原生答复。

集合代码交付由本仓发布，实际安装、新 MCP、Tavily 与根侧最终收尾仍由根任务执行；本记录不提前宣称整体完成。
