# P0 实施与核验

## 源修复

已修订权威 `templates/AGENTS.md.install`、workflow routing、FastCtx routing 与 Decision Grill：嵌套清单只描述其调用面；宿主直接工具按宿主真实声明和 owner 原生合同调用；保留 schema、权限、传输、服务、容量与命令错误。FastCtx Guarded 不触发 shell fallback 或关闭保护，Partial 按精确参数续页，明确下轮重试指令照原协议处理。

模板摘要已更新为 `c73dd09cb6fd26f2b31b286673a73251eb5a900625bb1e1b07f1ceb51a848326`，catalog 已同步该源声明。P0 已发布模板 `581dc2a3946e01e3634aa0dde59086c774d0f45d9bf11b65d39771c3a34c8aa4` 和本机旧 `AGENTS.md`/已发布 `a44dddc` 完整模板摘要 `8498d0dc121b483fc8e1f45cdbbfb49edf1f6b750c1bead6a0c252c699ec4191` 都保留在原生精确升级允许集，不覆盖未知内容。固定旧模板 fixture，复用此前更名升级测试并新增精确旧版本/用户改写边界。

## 已运行检查

- FastCtx routing 5 项、workflow routing 8 项、Grill 9 项契约测试通过。它们只证明文本合同，不是模型行为保证。
- lifecycle 全量 176 项测试通过，包含既有事务/静态/集合回归、精确用户模板升级/改写拒绝，以及第二集合的来源 identity、事务回滚、宿主 helper 信任和独立卸载测试。初次 fixture 多了一个末尾空行导致两项摘要测试失败；与发布 Git 字节核对后删除额外空行，未放宽摘要或拒绝合同。
- `git diff --check` 通过；按 `trellis-check` 复核实际模板→catalog→adapter→tests 调用链。

## 宿主行为证据

本会话的嵌套 `ALL_TOOLS` 没有 `request_user_input`，但宿主直接面声明了该工具。已直接调用 `functions.request_user_input` 获取最终验收报告呈现偏好，真实答复为“工具路由 P0”。该答复只调整报告篇幅，不是新实施授权。没有经嵌套清单探测、MCP 或 shell 代问。

本会话普通本地操作持续通过实际暴露的 FastCtx 执行。有界 inspect/grep 结果保留 Complete/Partial，发生 Partial 后使用回执的精确 files/offset 顺序续页；不存在因容量或读取失败切到 shell fallback。一次 component-versions 路径不存在后，通过 glob 找到实际 references 路径，保留的是路径错误，没有改报工具不存在。

首轮记录时尚未额外触发 Guarded，正式分发/安装仍待核验；后续结果见下节。历史真实直接 FastCtx 与 Guarded stub 证据见根研究 17，不用源码/契约测试冒充新恢复行为证据。

## P0 分发、容量恢复与实际落点

源提交 `1ce17133999cb21fd59e8439410373ac59a94d71` 已推送 `origin/task/matt-skills-extra`；作为可核验 P0 中间提交，尚未将整个任务合入 main。系统 installer 按固定 SHA 和 catalog 十二个路径、git 模式，下载到本次 staging。隔离目录 `/tmp/pennix-p0-validation-9r6xw4v0` 只保留本次夹具/回执/结果，不提交 Git。

真实容量探测使用本机 82,800 字节固定文本，无远端 WSL 操作。连续有界响应先由 350 行缩至 247 行、再到 7 行，末次 32 个单行范围 batch 实际返回 `Guarded burst stub`，明确内容扣留及下一轮重试原 inspect 请求。保留原参数，在后续轮次原样重试成功返回 32 个预期片段和准确 Partial 参数；另按 offset=8/limit=20 恢复窄读取。未使用 shell fallback、关闭保护、修改容量配置或在同轮循环重试 Guarded。

隔离使用实际下载树及现有 adapter 完成准备、事务接纳和 receipt match；仅 mock home 和两项 PATH 探针，避免临时命令目标与本机命令冲突。首次夹具 staging/目标不共用 parent 被拒绝，校正后 PATH 遮蔽又被拒绝，两次均发生在活动树切换前。成功切换后，旧 staging 的模块常量不能再用于静态处理；从新安装入口运行原生 `install/verify --component codex-agents` 后通过。没有改产品或放宽保护来适配夹具。

本机部署使用系统 installer 新建的同级 staging `.pennix-skills-stage-p0-ekq02cjx`，原生 staged lifecycle `replace-staged --component pennix-skills --yes` 成功，再从新安装入口 `upgrade --component codex-agents --yes` 成功。新原生 `verify` 分别针对 `pennix-skills` 与 `codex-agents` 均 `match`，`failures=[]`、`advisories=[]`。源模板、安装集合模板和 `/home/penn/.codex/AGENTS.md` 三者字节完全一致；用户规则已由宿主重新提供到当前会话，新增调用面条款实际出现。

P0 本次源修复、分发、精确旧模板升级和真实宿主交互/容量恢复已通过。提示词不提供模型永不犯错的确定性保证；schema/权限/传输/服务等类别的合同已审查，本轮没有人为制造凭据或网络故障来穷举注入。下一阶段可推进已批准的内容融合和双集合实现，最终仍需随完整发布重装及全范围回归收敛。

## Spec 判断与下一步

现有 quality spec 增补“已发布用户规则修订”测试惯例，防止用当前可变模板生成历史测试而破坏旧摘要证据；通用工具判断仍只落权威模板和路由 Skills，不在 spec 创建第二份全局规则。

第一轮的提交推送、隔离和本机接纳已完成；下一步为其余内容与双集合实现。旧源回退点为 `a44dddc1138ba673de0afc78fe9b94ca519b8df1`，旧完整模板 fixture 和摘要已固定；恢复沿 system installer staging/原生接纳，不手改安装树或回执。
