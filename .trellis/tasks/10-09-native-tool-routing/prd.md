# 收敛语义编辑入口与原生任务身份诊断

## Goal

核验SSH拓扑遗留两项观察，修复Pennix入口路由与全局规则，提交推送并通过lifecycle更新安装集合和本地落点。

## Requirements

- 只修复两项已核验观察对应的路由入口缺口，保持原生 owner、身份隔离和机械替换边界。
- 来源为根仓库 10-08-trellis-fastctx-session-task-binding 与 10-08-semantic-edit-tool-routing；不把未经证实的历史语义写入或正常身份拒绝称作运行时 bug。
- 用户明确授权规划后全量推进，无需额外审批；原生记录该例外依据，不捏造后续用户回复。
- 发布实际修改的 Skills 源码并受管更新当前设备安装集合、用户级 AGENTS；不改 Trellis/FastCtx 源码、凭据、Hook 或 SSH 拓扑。

## Acceptance Criteria

- [ ] workflow-routing、fastctx-routing、全局 AGENTS 对语义编辑和原生 task.py transport 无歧义。
- [ ] 身份缺失和身份存在但任务未绑定有安全可执行的诊断路径，不猜造 identity/pointer。
- [ ] 既有路由、集合/静态模板测试和 Skill 验证通过，目录/模板摘要一致。
- [ ] main 提交推送完成，明确发布提交的完整 Skills 集合受管重装；块外内容保留，安装验证通过。
- [ ] 本轮临时产物清理，源 task 与根侧验收可追溯。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
