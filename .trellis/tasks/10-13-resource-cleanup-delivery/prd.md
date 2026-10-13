# 落实工作流资源清理 Skill

## Goal

执行根任务 revision 2 已批准的清理 Skill、资源矩阵、来源快照与生命周期注册，验收安装集合

## Requirements

- 继承根任务 revision 2 的 D7–D9、R1–R5/R8：新增清理指导、资源矩阵和结果合同，注册 routing/lifecycle。
- 补齐各组件职责与保留边界，不新增通用执行脚本；Grok 物化文件必须与 catalog 精确来源一致。
- 只修改源码集合；安装集合由 system installer 暂存后，公开 lifecycle replace-staged 接纳。

## Acceptance Criteria

- [ ] Skill 有效、引用可解析；未知 owner、活动资源、无原生入口和部署证据不足均停止执行。
- [ ] 预览与实际结果分离，授权范围不扩大，资源矩阵覆盖批准范围。
- [ ] lifecycle 全量测试、安装收据和集合核验通过；提交推送与根侧记录一致。

## Notes

- 授权来源：根任务当前 revision 2 的用户明确批准；本任务仅补齐既定范围执行落点。
- 已推送 `71ed1c8` 是首批实现；此前未及时建立组件任务，不回写虚构历史状态。
- 回滚：按已核验旧来源重建暂存集合后，走公开 replace-staged；漂移状态先恢复，不重写收据绕过。
