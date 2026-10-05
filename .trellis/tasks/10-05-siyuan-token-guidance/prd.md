# 补充思源API Token原生获取指引

## Goal

承接根思源集成任务及用户当前明确授权：修正设置→鉴权→API token位置，补充lifecycle终端提示与源说明，原生发布安装并验证连接；不改变凭据或数据协议。

## Requirements

- 在lifecycle的现有SiYuan隐藏Token录入提示与SKILL说明中明确实际入口：目标思源内核的“设置 → 鉴权 → API token”。
- 区分网页登录密码、模型API Key与思源API Token；连接NAS时从NAS网页取值，其他客户端的独立Token不能替代。
- 连接reference/README与用户静态指引一致；使用现有adapter，仅修改指引，不改凭据/配置schema或增加依赖。
- 根任务和本轮用户已明确授权实施、推送与原生安装；主会话main直接交付，不派发implement/check。
- 验证先执行相关假凭据回归、source collection检查及diff检查，提交推送，再系统SkillInstaller全集合staging/native replace-staged和全量local verify。保留现有真实连接，不重新录入Token。
- 服务测试必须通过已绑定的SiYuan原生工具；宿主工具未加载时保留capability-gap，由根任务承接重连和数据/索引验收。

## Acceptance Criteria

- [ ] 正确入口在源lifecycle终端提示、Skill说明、连接reference和README一致。
- [ ] 既有连接/header安全回归与collection检查通过，源码main提交推送。
- [ ] 原生完整集合安装及local verify通过，已有siyuan-connection仍enabled/configured，源任务按自身AC归档；根任务记录真实服务测试层级。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
