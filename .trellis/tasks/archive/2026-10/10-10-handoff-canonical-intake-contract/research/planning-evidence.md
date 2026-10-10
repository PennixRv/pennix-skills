# 规划证据与限制

## 已核验

- 根审计 `.trellis/tasks/archive/2026-10/10-10-handoff-scale-read-contract-audit/research/findings.md` 已记录两个验证复现、大包统计和限定；本轮不重读原始 rollout 或宣称代理全文已读。
- 生产搜索 conversation_candidates、conversation.timeline、core_read、handoff.py 和 render_handoff_prompt.py：消费位置仅在本 Skill 的入口、三个脚本和两份测试，未发现其他 Skill 生产调用方。
- handoff.py:446–458 同时序列化 source.rollout 与顶层 conversation；:465–545 校验消费结构不完整；render_handoff_prompt.py:103、:147–156 使用顶层 conversation。
- 归档 :985–1033 要求严格 core/prompt 配对；保留 :1149–1205 只复制或移除该配对。归属 :942 起传递整个 JSON 摘要给原生 Trellis。保留单文件表示可沿用这些接口。
- schema :27–30 当前 9、支持 8/9；:602、:947、:1217 使非当前包只读。渲染器拒绝覆盖不同 prompt；旧包/收据保持已有测试。用户随后取消旧语义兼容，当前设计不维护 schema 9 写流程。
- main/远端跟踪头为 7d1211ae2f9788e2bdd30db7f073fa0c343a4d48；origin 为 https://github.com/PennixRv/pennix-skills.git，只有本任务未跟踪规划文件。现有交付沿 main，tag 列表为空；verify.yml 在 push/PR 枚举所有 Python Skill 测试，没有独立软件包发布要求。
- 唯一 lifecycle catalog 的 collection_contract 声明 PennixRv/pennix-skills/main 和 12 个路径；系统 skill-installer 支持精确 --ref、--method git 和新 --dest。原生 replace-staged 参数及 scoped verify 入口已通过 --help 核验。
- 本机 discover（2026-10-10T03:39:20.409650Z）显示 Arch/WSL2 支持、pennix-skills match、完整性 match、PyYAML ready、无缺失成员、命令链接 match、staging none。安装路径为 /home/penn/.codex/skills/pennix-skills。
- 根最近交付 acceptance 固定已安装产品 d7bb1852a81bfd595631b96f39918fcb7468dd89；后续 7d1211 仅任务/日志，skills 树一致。实施前再次核验动态状态。
- 根无 remote；当前有效根文件未提供 pennix-skills Gitlink 或版本清单。旧 issue 中提及的 `workflow-components.json` 等已不存在；不以历史描述恢复退役清单，来源固定回本任务 acceptance。
- discover 另报 tmux 版本和未启用 Grok 配置漂移；本任务不处理这些私有/无关目标。

## 确定程度与待验收

设计方案、schema 10、read 和新声明尚未实现；无损分页、异常拒绝和大小改善必须用实施后实际产物验证。原有测试在前序审计通过，不代替新版本验收。程序结构检查不能证明摘要完整或代理理解全部文本。

唯一下一步：三份方案核验封口，展示并等待用户随后明确批准；不执行产品修复、发布或安装。
