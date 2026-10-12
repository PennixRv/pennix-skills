# Matt 精选集合与 Pennix 规划路由融合

## Goal

实施根任务 revision 3 已批准的 Pennix 范围：宿主工具调用面 P0、决策地图方法、工作流写作差集和 lifecycle 双集合；不增加独立产品决策。

## Requirements

- 修复嵌套编排器工具清单被错误当作宿主完整清单的问题，覆盖用户规则源模板、通用路由、FastCtx 与原生交互专项入口；保留真实错误类别和原生协议边界。
- FastCtx Guarded 容量提示按有界读取、精确续页和明确的下轮重试处理，不触发 shell fallback，不关闭保护或扩充共享池。
- 在现有 Grill 中融合术语情境核对和决策地图方法；在现有中文写作参考中融合常驻/条件引用成本与同概念共置方法，不新增 Skill 或任务状态机。
- lifecycle 接纳固定 SHA 的公开 `PennixRv/pennix-skills-extra` 十项精选目录；新集合独立 managed install/upgrade/verify/uninstall，旧集合继续 native-owner 合同。
- 新集合来源、目标、receipt 与事务完整可核验；拒绝未知目标/来源/漂移，失败保留旧树/receipt和其他集合。
- 提交推送、隔离安装验收后本机安装核验；根侧关联精选 SHA、Trellis 发布和实际宿主集成证据。

完整需求和决策来源为根仓库 `.trellis/tasks/10-12-matt-skills-pennix-lifecycle-plan/` 的 revision 3。此任务只执行该已展示、封口并获用户明确批准的 Pennix 修改面，不产生独立方案取舍或扩大范围。

## Acceptance Criteria

- [ ] 用户规则模板、各路由 Skill、分发摘要和目标安装规则一致；真实宿主调用证据能区分嵌套缺项、宿主缺失、执行错误与容量保护。
- [ ] Grill 决策地图、术语核对与写作方法差集落到现有自然入口，保持 owner/原生任务生命周期。
- [ ] catalog 精确十项、原始路径与 40 位 SHA，未经审核的来源/路径/名称不能进入安装。
- [ ] 新集合 install/upgrade/verify/uninstall、幂等、漂移拒绝、故障回滚和跨集合隔离行为测试通过；旧 Pennix 全量回归通过。
- [ ] 源提交已推送，隔离和本机安装核验通过，源/安装/回滚点记录齐全；真实发现或触发受限时记 blocked，不宣称完成。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
