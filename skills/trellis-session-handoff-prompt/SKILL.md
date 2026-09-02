---
name: trellis-session-handoff-prompt
description: 仅在当前用户明确要求正式交接提示词，且当前项目的 handoff validate 返回 ready 后使用。
---

# Trellis 交接提示词

先由项目的 `session-handoff` Skill 完成正式交接请求和校验。本 Skill 只调用当前项目的
`.agents/skills/session-handoff/scripts/handoff.py validate`，不创建、修复或消费交接包。

普通工作、重启、暂停、会话变长、验收失败、provider 失败、压缩、等待和句柄丢失都不触发。
只有校验状态为 `ready` 时才输出有界的新会话入口；其他状态停止生成提示词并按项目事实处理。

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/trellis-session-handoff-prompt/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root>
```

该 Skill 不读取对话、凭据、缓存、日志或运行时台账，也不改变 task、Issue、Git 或 worker 生命周期。
