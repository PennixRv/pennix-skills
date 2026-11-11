# 接入思源人工知识与晋升路由

## Goal

承接根任务10-05-siyuan-knowledge-workflow-design及2026-10-05实施授权；实现原生MCP headers、可选连接、知识Skill、晋升路由与安全验证，发布安装并清理活动残留。

## Requirements

- 原生 MCP，无数据代理；人工保存与晋升，任务/交接解耦；默认 notebook 由私有连接记录指定。
- stdlib headers helper、安全私有记录和可选 lifecycle target，保留用户无关配置及上游权限。
- 根设计已授权实施、发布、安装和清理；不重复 gates。

## Acceptance Criteria

- [x] helper/adapter 安全行为与现有 lifecycle/collection 回归通过（82 项）。
- [x] source main 797cb95 提交推送；系统原生 installer 全集合安装、replace-staged 和全量 local integrity 验收通过。

服务握手、Penn 索引与原生读写验收属于根协调任务，本源码任务不把安装完整性等同于服务验收。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
