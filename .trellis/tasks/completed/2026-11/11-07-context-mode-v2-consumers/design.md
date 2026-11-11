# Context Mode v2 消费方设计

## 范围与已批准依据

根任务 `.trellis/tasks/in_progress/11-07-context-mode-routing-upstream-audit` 的 design.md、implement.md 与 implementation-approval.md 为跨 owner 合同；最终 artifact revision 为 `9dcd2501d825910bb3e5b717688a9633d0d0c4c8479df9e1e71e6fdac24814cf`。用户指示“最后再检查一次方案的完整性和健壮性，之后就可以开始进入实施和收敛阶段了”及“继续”，已涵盖本组件的以下变更，不重新索取相同授权。

## 接口与取舍

删除独立集成 Skill，以 pennix-workflow-routing 导航原生宿主、来源 owner 和按需文本处理；不复制上游命令指南。小输出与原生调用有效，失败仅对本次调用选择回退，权限拒绝不绕过。项目外指令仍直接原生全文加载；Skill 路径从宿主声明展开，保留集合层级。

集合 manifest 是唯一成员权威。资源清理指向 v2 原生 ctx_purge 并明确共享项目范围；三个用户命令由 Context Mode/Lifecycle 交付，不进入集合。真实评估继续使用现有 runner，候选 CODEX_HOME 由 Lifecycle 物化，验证来源后执行，不将 --phase 标签当版本切换。

## 验证、风险与回退

先 collection verify 与受影响 unittest，再固定 before/after 的真实模型调用。原始 trace 留在临时目录，不提交秘密或运行态。无真实行为证据不声明通过；压缩恢复由 Context Mode 的真实 app-server 验证承载。源码可回退到起点 5cfe7adb61ddd585a6f65574b5aec6fb1c6c3c49；安装回退由 Lifecycle receipt 承担。需先发布集合提交，再更新 Lifecycle catalog 固定 SHA；不直接改安装副本。
