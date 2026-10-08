# 语义编辑路由核验与方案

## 事实分类

- WF-TOOL-01 是用户观察；可取得的历史证据未证明具体语义代码写入走 FastCtx。历史标题的机械 replace 合法，后续 apply_patch 有直接记录。
- 本轮前序 followup 任务创建曾通过 FastCtx run 调 task.py create/list，属于可证实的 owner transport 偏离。
- 当前 fastctx-routing 已写明语义代码用 apply_patch，但上层 workflow-routing 的表把“普通本地文件”整体放进 FastCtx，没有显式语义编辑行；全局 AGENTS 的 FastCtx 块也没有在未加载详细 Skill 时暴露该例外。这是可修复的入口规则缺口，不能断言它唯一决定了历史模型行为。

## 最小变更与所有权

pennix-skills 源码负责三层一致的指引：
1. 用户级 AGENTS 受管块：语义源代码/配置/文档创建修改用原生 apply_patch；专用 owner 自行生成的资产仍由 owner 写入；确定性机械批量替换保留 dry-run 与上限。
2. workflow-routing：原生协议先行，语义编辑显式路由 apply_patch，普通只读/检索/构建/测试保留 FastCtx。
3. fastctx-routing：补齐配置/任务文档与写入脚本的边界、身份缺失时换回正确原生调用路径的诊断。
不新增工具拦截 Hook、代理服务或路由脚本；不编辑安装副本，catalog 模板摘要随源模板更新。两个根任务分别验收，同一个组件 task 只实现一次。

## 验收与边界

运行既有路由和 lifecycle 静态模板/集合测试，Skill quick_validate；检查补丁及实际受管安装。真实使用 apply_patch 编辑本轮源码，原生 task.py 操作本轮状态，机械 replace 仍合法。静态合同检查不能证明所有未来模型调用必然遵守；本轮不将提示词改进报告成运行时强制拦截。
## 授权与执行边界

2026-10-09 用户明确要求在 Paseo 清理后继续这两个既存任务，先核验真实性，再形成方案并推进提交、推送、安装和关联资产更新；原文包括“我想也不需要我额外审批，我直接批准你按照你认为的最佳时间全量推进”。这是针对本轮的显式委托和免除额外审批，不宣称用户在看见新封口后又回复过。仍先完善资产、原生 seal/approve/start；审批 basis 如实引用本轮授权。无并行子节点，无新增 Hook 或身份兼容桥。

身份核验结论见根侧对应 design.md；当前原生宿主有 CODEX_THREAD_ID、FastCtx 服务进程没有，两者不应被混为同一个执行环境。

