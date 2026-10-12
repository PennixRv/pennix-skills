# P0 实施与核验

## 源修复

已修订权威 `templates/AGENTS.md.install`、workflow routing、FastCtx routing 与 Decision Grill：嵌套清单只描述其调用面；宿主直接工具按宿主真实声明和 owner 原生合同调用；保留 schema、权限、传输、服务、容量与命令错误。FastCtx Guarded 不触发 shell fallback 或关闭保护，Partial 按精确参数续页，明确下轮重试指令照原协议处理。

模板摘要为 `581dc2a3946e01e3634aa0dde59086c774d0f45d9bf11b65d39771c3a34c8aa4`，已更新 catalog 源声明。核验本机旧 `AGENTS.md` 与已发布 `a44dddc` 完整模板均为 `8498d0dc121b483fc8e1f45cdbbfb49edf1f6b750c1bead6a0c252c699ec4191`；将该已知旧摘要加入原生精确升级允许集，不覆盖未知内容。固定旧模板 fixture，复用此前更名升级测试并新增精确旧版本/用户改写边界。

## 已运行检查

- FastCtx routing 5 项、workflow routing 8 项、Grill 9 项契约测试通过。它们只证明文本合同，不是模型行为保证。
- lifecycle 全量 163 项测试通过，包含既有事务/静态/集合回归和新增精确用户模板升级/改写拒绝。初次 fixture 多了一个末尾空行导致两项摘要测试失败；与发布 Git 字节核对后删除额外空行，未放宽摘要或拒绝合同。
- `git diff --check` 通过；按 `trellis-check` 复核实际模板→catalog→adapter→tests 调用链。

## 宿主行为证据

本会话的嵌套 `ALL_TOOLS` 没有 `request_user_input`，但宿主直接面声明了该工具。已直接调用 `functions.request_user_input` 获取最终验收报告呈现偏好，真实答复为“工具路由 P0”。该答复只调整报告篇幅，不是新实施授权。没有经嵌套清单探测、MCP 或 shell 代问。

本会话普通本地操作持续通过实际暴露的 FastCtx 执行。有界 inspect/grep 结果保留 Complete/Partial，发生 Partial 后使用回执的精确 files/offset 顺序续页；不存在因容量或读取失败切到 shell fallback。一次 component-versions 路径不存在后，通过 glob 找到实际 references 路径，保留的是路径错误，没有改报工具不存在。

历史真实直接 FastCtx 与 Guarded stub 证据见根研究 17；本轮尚未额外触发 Guarded，不用源码/契约测试冒充新恢复行为证据。源修复和原生交互已通过，正式分发/安装、受管落点和剩余容量场景仍待核验；P0 尚未宣布整体通过。

## Spec 判断与下一步

现有 quality spec 增补“已发布用户规则修订”测试惯例，防止用当前可变模板生成历史测试而破坏旧摘要证据；通用工具判断仍只落权威模板和路由 Skills，不在 spec 创建第二份全局规则。

下一步：提交推送 P0 源提交，按 system installer 创建明确本次 staging，隔离验收后经 lifecycle 接纳本机集合并原生升级用户规则；保留源 pin/旧回退点，再继续其余内容及双集合实现。
