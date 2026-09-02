---
name: trellis-session-handoff
description: 仅在当前用户明确要求正式跨会话交接时，转入当前项目提供的 session-handoff Skill；普通重启、压缩、等待或失败不触发。
---

# Trellis Session Handoff

这是用户级路由说明，不实现第二套交接协议。交接文件、任务快照和校验逻辑必须由当前项目的
`.agents/skills/session-handoff/` 维护；项目没有该 Skill 时，不得猜测、自动创建或从历史对话重建交接包。

只有当前用户明确要求正式跨会话交接或正式交接恢复时，才可进入项目 Skill。普通工作、重启、暂停、会话变长、
验收失败、provider 失败、压缩、RecoveryBrief、等待和句柄丢失都不授权写入交接文件。

在本项目中使用：

```bash
python3 .agents/skills/session-handoff/scripts/handoff.py --project-root . \
  write --request <request.json> --explicit-user-request
python3 .agents/skills/session-handoff/scripts/handoff.py --project-root . validate
```

`validate` 的结果只是项目事实核验；`ready` 不代表获得实施授权，`changed`、`absent` 或
`recovery_required` 都必须按项目实时事实处理。该入口不改变 task、Issue、Git 或 worker 生命周期，
也不复制对话、凭据、缓存或运行时台账。
