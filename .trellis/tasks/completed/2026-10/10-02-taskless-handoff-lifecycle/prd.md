# 修复无任务交接封口与会话身份使用

## Goal

增加无任务正式交接封口，使用 Trellis 原生 session_source，保持 AgentMemory 证明与任务所有权门禁；更新交接 Skill、回归验证、提交推送重装。

## Requirements

- 在main修复无任务默认AgentMemory交接：独立session_source、taskless seal、同源接收拒绝，保留有任务ownership。
- proof中断恢复不重复POST，精确content/project/id与有界分页；registry参与项目身份，同名根冲突拒绝。
- 既有lifecycle static目标管理固定npm pair、Node env-file、禁用floating plugin MCP；秘密不进TOML。
- 官方hooks保持原生，明确父环境启动要求、共享召回和上游local fallback边界，不fork、不改模型/4096/增强开关。

## Acceptance Criteria

- [ ] meaningful Python回归、collection smoke、真实MCP握手与官方hooks canary；当前host真实自动触发限制如实记录。
- [ ] commit/push/reinstall，与根协调任务10-02-agentmemory-integration-and-handoff-convergence组合验收后archive。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
