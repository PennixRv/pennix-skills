# 切换 FastCtx 路由并移除 context-mode 旧边界

## Goal

更新 `pennix-skills` 的工作流路由，使 FastCtx 成为本地操作聚合、输出有界化和长命令/job 的唯一候选，同时移除已退役 context-mode 的活动路由表述。将独立的 Windsurf 语义代码搜索 Skill 统一命名为 `windsurf-code-search`，避免与 `fastctx` 混淆。保持 Windsurf Code Search、CodeGraph、OpenViking、Trellis 和 handoff 的既有职责，不新增 FastCtx 包装 Skill、Hook 或权限模型。

## Requirements

- 将未知规模的本地读取、递归搜索、文件发现、构建/测试输出和长命令路由到 FastCtx 的有界工具或 job。
- FastCtx 不承担代码生成、语义编辑、OpenViking 记忆、Trellis task/ownership、handoff、CodeGraph 或生命周期协议。
- FastCtx 不可用时直接降级到宿主原生工具，不恢复 `ctx_*` 路由。
- `windsurf-code-search` 仍只在本地检索与 CodeGraph 无法定位模糊语义时返回候选，并且候选不写入 FastCtx、OpenViking、Trellis 或持久索引。
- CodeGraph setup 不依赖 context-mode 的目录保护。
- 不修改 Windsurf Code Search 的触发条件、远端协议或凭据处理；仅更新其用户可见 Skill 名称；不修改 FastCtx、OpenViking 或其他第三方源码。

## Acceptance Criteria

- [x] 路由 Skill 不再把任何本地操作、输出处理或生命周期交给 context-mode/`ctx_*`。
- [x] 路由 Skill 明确 FastCtx 触发范围、原生降级和不得承担的工作流职责。
- [x] Windsurf Code Search 与 CodeGraph Skill 的 context-mode 过时边界已清理，现有路由测试通过。
- [x] Skill 元数据和包内容校验通过，工作树无凭据、运行态或生成缓存。
