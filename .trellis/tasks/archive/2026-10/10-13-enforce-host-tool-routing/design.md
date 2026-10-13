# 实施设计

## 修改边界

本子任务只修改 `pennix-skills` 源仓库。权威用户规则源是 `skills/pennix-component-lifecycle/templates/AGENTS.md.install`；既有 `pennix-workflow-routing` 合同测试负责锁定模板表面。宿主运行时、MCP 服务、安装副本和 Trellis 源码不在本子任务修改。

## 规则

调整工具职责段现有的工具可用性规则为：

> 工具可用性以当前宿主实际声明和真实调用结果为准。严禁将 `functions.exec` 的 `ALL_TOOLS` 当作宿主直接工具清单；它只描述嵌套调用面，缺项不能证明宿主直接工具不存在。宿主已声明所需工具时，必须通过其原生入口调用。调用失败不等于工具缺失；保留原始回执，后续动作遵守负责组件的合同。

既有宿主声明、嵌套调用面、真实回执和调用失败分类继续保留。该静态合同不能证明模型行为；无宿主级回归接口时明确记录限制。

## 版本与验证

- 重算 `codex-agents.template.revision` SHA-256。
- Trellis beta 发布后才把 `trellis-cli.approved_version` 更新为真实精确版本。
- 运行 routing、lifecycle 和中文写作 Skill 既有测试，核对安装预览、模板摘要、暂存替换和 `codex-agents` 原生 upgrade 的收据。
