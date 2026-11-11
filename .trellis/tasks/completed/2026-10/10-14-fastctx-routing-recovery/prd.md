# 修正 FastCtx 路由恢复与参数误用根因

## Goal

承接根任务 `/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-14-fastctx-output-pool-recovery`，修正 `pennix-fastctx-routing` 对 FastCtx 容量恢复的错误约束，并从调用域、工具 schema、Skill/模型说明和实际参数构造链追踪 `failed to deserialize parameters` 的误用根因。保持规范参数唯一权威，不增加兼容别名。

承接根任务 fastctx-output-pool-recovery，修正 pennix-fastctx-routing 对 FastCtx 容量恢复和规范参数的错误约束；不做参数别名兼容，追踪调用域、工具 schema、Skill 说明和实际参数构造的误用根因，更新路由合同测试并按原生生命周期发布物化。

## Requirements

- R1：容量不足或分页不得被路由说明解释为当前工作结束、必须等待新用户消息或工具缺失；沿准确 cursor 在当前工作链继续。
- R2：保留 FastCtx 与 Trellis、交接、原生交互、外部检索、部署及语义编辑的职责边界，不把容量提示转成 shell fallback。
- R3：不接受 `path`/`file_path`/`query` 等参数别名；规范字段、工具 schema 和错误提示必须一致。
- R4：从实际调用域、工具 owner、schema、Skill/模型说明和参数构造位置定位误用来源；只修正 Pennix 所有的说明、路由和合同测试，不代改 FastCtx 源码。
- R5：路由说明不得要求同轮禁止继续，也不得鼓励忙循环；明确区分只读分页恢复与已执行命令的副作用保护。
- R6：源 Skill、测试、版本/来源记录和安装物化路径保持单一 owner；不修改安装副本、用户配置、凭据或根项目 AGENTS。

- TBD

## Acceptance Criteria

- [ ] AC1：`pennix-fastctx-routing` 不再把 Guarded 容量提示解释为必须进入下一用户轮次；读/搜/批量分页可在当前工作链按准确参数继续。
- [ ] AC2：保留协议排除、工具可用性判断、Partial 精确续读、命令不盲目重跑和真实错误分类。
- [ ] AC3：规范参数说明和测试覆盖当前真实字段；不接受别名，不通过字符串兼容掩盖调用来源混淆。
- [ ] AC4：错误调用来源、实际 owner、修改提交和验证结果记录在本任务；不把 FastCtx 源码问题伪装成 Pennix 文案修复。
- [ ] AC5：源侧测试、发布来源、安装物化和实际新会话验证按 lifecycle 合同完成；未安装或未验证不宣称完成。

- [ ] TBD

## Notes

- 当前任务由 `task.py create --no-start` 建立，处于 planning；没有启动、seal 或实施批准。
- FastCtx owner 任务为 `/home/penn/devel/fastctx/.trellis/tasks/10-11-codex-native-nesting`，已由原生 `task.py replan` 回到 planning；本任务依赖其已验收的服务端合同，但不复制组件源码。
- 用户已确定：取消轮次累计池、取消单次 9,000/10,000 强制覆盖、不做参数兼容而追查根因。

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
