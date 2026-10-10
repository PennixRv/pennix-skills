# 规则与 Skill 文档修订设计

## 用户级最小规则

在 `skills/pennix-workflow-lifecycle/templates/AGENTS.md.install` 的“沟通与文档”说明新增技术文档的语言默认值。建议完整条目：

> 新增技术文档默认使用简体中文，明确语言要求除外；不因这条规则追溯重写既有文档。Trellis 资产先遵守其格式合同。

保留相邻的自然行文、准确术语、原文标识和事实风险规则。职责入口继续短索引 `pennix-chinese-tech-writing`，不在全局模板展开文档种类、Trellis schema 或思源保存方法。不是为每种文件增加规则。

## 写作方法与载体

`pennix-chinese-tech-writing` 的 description 与正文改用准确中文，明确默认语言只决定新写内容，不授权保存、部署、自动捕获或全量重写。其格式优先说明首先保留用户与目标项目合同。

新增一份有实际用途的载体参考 `references/workflow-assets.md`，由入口按内容加载：分别说明 Trellis 任务/规范、用户规则/Skill、思源技术笔记的可读正文与不可改机器结构，并指向实际负责 Skill。保持短小，不复制任务阶段、审批状态或 SiYuan API。

现有 4 份中文写作参考逐项复核；不机械移植英文受控语言、固定句长或全局禁词，不把可接受引号和称呼设为失败。MIT 与固定上游来源保留；新增本地参考及适配事实写入 `UPSTREAM.md`。

## 全集文档

本组件直接维护 10 个成员；Grok Search 与 Windsurf Code Search 由各自独立来源维护。本轮入口、执行参考及现有界面元数据共 34 个已有文件，完整逐项复核，但没有“每文件必须改”或统一篇幅目标。

英文可读内容改为中文；原 name、字段、选项、枚举、路径、固定日志、正式名称和许可保留。中文入口核对触发、否定、调用、失败、授权、风险和跨 Skill 合同。当前共同检查维度 C1–C9 及逐成员重点在根任务 `review-matrix.md`；本任务另在未封口执行记录保存实际结论，不用入口长度证明质量。

较长的 lifecycle、handoff、project-update 等入口仅在独立使用场景确实需要时移出细节到参考；关键安全、触发和停止条件留在入口。新增参考须可达，不能改为默认读取整个集合或复制组件协议。

现有界面文件沿原结构修订，可读提示采用中文；保留工具正式名称与 `policy`。所有现有 `default_prompt` 必须包含正确 `$skill-name`，`short_description` 按系统指南的 25–64 字符核对。没有界面文件的成员不因此新增文件或默认提示。

## 职责一致性

- 写作默认值不授权新建 Trellis 项目、写入思源或正式交接。
- `pennix-fastctx-routing` 继续排除语义编辑、原生任务/Channel、检索和部署，FastCtx 的实际 MCP 清单与编排器清单区别保留。
- `pennix-decision-grill` 继续筛选重要用户取舍和依赖轮次，阻塞宿主交互、取消合同、后续批准和原生 replan 条件不改变。
- `pennix-workflow-routing` 保留一次检索降级、独立证据、当前任务与知识来源的区别，只索引方法，不复述完整协议。
- `pennix-siyuan-memory` 的写入参考与路由索引说明新增技术笔记默认中文，仍需具体用户保存意图、原生写入、并发核对及回读。
- Grok/Windsurf 的原生内部重试是实际组件能力，代理是否重新调用或切换供应商仍由宿主合同决定。相关文档分别说明，不能为了用词一致删掉已有受控运行行为。

## 正式交接生成器

修改 `skills/pennix-session-handoff/scripts/render_handoff_prompt.py` 的 Markdown 可读模板，默认中文。保留现有 parser、JSON 字段、标识、状态、历史内容和 `_atomic_prompt` 覆盖保护；不加旧英文模板或语言参数。

新中文提示词逐条保留原准入和继续流程：结构校验、完整配对读取、启动核对、当前事实 reconciliation、初次准入禁止执行、后续明确授权后的 claim 与真实阶段继续。语义精炼不压缩授权条件。已有英文 prompt 不迁移、覆写或承诺同路径继续渲染；原生不同内容拒绝仍正确。schema 8 历史只读分支不改。

必要测试验证实际可观察行为：新中文文档和不变机器字段、同版幂等、未就绪无写入、不同/旧英文文件拒绝覆盖且字节不变、历史只读。不能仅新增一个“包含中文标题”断言就宣称整个交接安全。

## 来源、部署与更新

Grok 来源文档任务 `docs/tasks/2026-10-10-chinese-skill-guidance.md`，Windsurf 来源任务 `.trellis/tasks/10-10-chinese-skill-guidance/`。来源文件提交推送后再更新本集合 catalog 的 ref/commit；按现有 `archive` / `npm-pack` 机制核对快照，`sync-collection.yml` 不需要新增语言覆盖机制。

用户规则模板变化后，catalog 保存新 SHA-256；当前完整旧模板摘要 `57eda055881bdd719bd9e72e9d94e009d74b99beac20fc55687b22974689268d` 加入原有安全迁移允许列表。D2 硬切限于旧英文交接渲染，不删除安全的全局模板升级能力。

集合提交交付到 Git 后，系统 Skill 安装器固定产品提交、按 catalog 路径安装到同级 staging，验证后原生 `replace-staged`；再用新 lifecycle 原生升级 `codex-agents`。回执、用户配置、缓存和运行态不手改、不提交 Git。纯文档的来源成员不单独升 CLI 或二进制版本；本集合及交接脚本由精确提交交付。

## 完成限制

当前只编写规划资产，尚未改产品或部署。后续批准必须覆盖根与本组件展示的当前实质方案，不能拿前序批准开始。本轮没有外部收费检索、思源写入、新设备或新会话模型路由行为保证；若未动态验证，最终如实标记。
