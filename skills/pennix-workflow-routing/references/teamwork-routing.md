## 当前 Trellis fork 并行工作流

本节只分流入口，Teamwork Session、teammate、assignment、报告与处置由当前 `trellis-teamwork` 和原生 CLI 管理。

1. 按项目当前执行模型和实际授权选择主会话、宿主原生代理或只读 Teamwork；可用工具与角色不同，不相互冒充，也不强制派发。
2. Teamwork teammate 通过角色合同只提供报告，不写源码、主任务事实或接受结果。主代理核验证据、受保护目标和接受条件后记录处置；执行结束不等于验收通过。不新增 sandbox 或权限隔离门槛。
3. general 是协作模式，batch 是需要已验证 adapter 的受控入口。未具备 adapter 就明确拒绝 batch，不用交互 run/spawn 替代；模型和 reasoning 配置读取当前原生 profile，不写死旧映射。
4. 派发、等待、恢复、资源处置及临时任务选择均使用当前 Trellis 原生接口。身份、归属、阶段和实施授权分别核验；不伪造状态、复制旧队列协议、用轮询替代原生等待或自动重启已停止任务。普通继续与压缩恢复沿已知断点推进。
