# 实施与验收计划

当前只保留计划，未通过本任务的 Planning Seal，也未获得实施批准。实际修改由 Pennix owner 在主会话完成；不创建实现/检查子节点。

## P0 规划准入

1. 复核根任务 `fastctx-output-pool-recovery` 与 FastCtx `10-11-codex-native-nesting` 的当前修订、owner、Git 基线和发布前置。
2. 读取本仓库适用的规格、既有 Skill 测试、生命周期入口和来源记录，确认修改只落在 Pennix 源侧。
3. 补充实际工具 schema 与误用调用链证据，确认没有应由 FastCtx 或宿主 generator 负责的缺口被错误归到 Skill。
4. 完成本任务 planning 资产、原生 plan seal，展示当前版本并等待本任务后续明确批准；不因根任务批准或 FastCtx 任务批准自动开始。

## P1 Skill 与合同测试

1. 删除“容量提示要求下一轮且同轮不重试”的规定，改为当前工作链内按实际恢复参数继续、收窄或记录真实阻断；保留避免无界忙循环的原则。
2. 在现有适用段落补充规范参数的唯一字段名和调用来源要求；不加入别名、不自动重写、不静默忽略未知字段。
3. 调整 `tests/test_contract.py`：保留入口边界、ALL_TOOLS 误判、Partial 精确续读和协议排除合同；删除过时的“禁止同轮续读”正向断言，增加规范字段和不兼容别名的静态门。
4. 若现有测试需要读取 FastCtx 源码或运行态才能证明行为，改为记录对应 owner 的行为验收引用，不把 Pennix 字符串测试冒充端到端通过。

## P2 质量与行为验证

1. 运行 Pennix 现有 Skill 合同、语法和适用生命周期检查，执行中文文案只读检查；区分 warning 与失败。
2. 待 FastCtx owner 发布修复后，使用实际新 MCP 连接核验 V01/V07/V08：连续分页不需要新用户消息，规范字段成功，别名明确拒绝，错误路径准确，FastCtx 容量/宿主截断不被报告为工具缺失。
3. 验证普通命令和具有副作用的工具不会因容量提示自动重跑；验证 Trellis、外部检索、交接和部署仍走各自原生入口。
4. 若行为和 Skill 语义不一致，先回 owner 任务 replan，不用修改说明掩盖服务端问题。

## P3 发布与物化

1. 提交前复核只改本 Skill、测试和必要来源记录；不带入根任务、凭据、缓存、运行态和安装副本。
2. 通过源仓库规定的测试后提交、推送并固定精确 commit；已有发布版本不覆盖。
3. 使用 `pennix-component-lifecycle` 的原生 staging/replace 与 receipt 物化源 Skill；验证安装副本字节与源 commit 对应。
4. 在根任务记录源提交、安装来源、实际行为检查和未运行/受限门；根侧离线组合门不得写入或模拟组件状态。

## 回滚与收敛

回滚使用上一个已验收 Pennix 源提交和 lifecycle 原生 replace/receipt，不能手改安装副本或用户配置。若 FastCtx 服务端尚未发布或其 schema 仍不一致，Pennix 任务保留 `blocked`/`not_run` 证据，不把 Skill 文案更新宣称为完整修复。全部 AC、owner 来源、物化和根组合验收通过后，按原生 `task.py finish/archive` 收敛本任务。
