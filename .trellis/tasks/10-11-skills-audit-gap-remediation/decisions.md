# 组件设计决定

## D1：原生职责保留

- 根任务 D1 原生实际答复：“保留原生归属 (Recommended)”。
- lifecycle 只负责系统部署和已声明配置；CodeGraph 项目初始化/配置与通用用户 Hook 修改保留原生所有者。
- 修正 routing/lifecycle 误导语句；检查全部实际调用者后，清理冗余 CodeGraph/Hook/Trellis helper 及仅针对它们的测试，不新增公共 adapter 接线，不改变原生组件或用户配置。
- 本任务保持 planning，设计答案不授权产品编辑或 start。

## D2：历史秘密检测

- 根任务 D2 实际答复：“脱敏后继续 (Recommended)”。
- 已检测的历史秘密去除并明确标记，保留事件、顺序、来源和非秘密上下文；摘要、事实、收据检测命中仍拒绝。
- 修复 JSON 字段引号/转义及已知 token/xai 等覆盖遗漏；逐结构化值检查，不能用序列化整个对象代替值级处理。
- 不修改源 rollout，不保证识别任意未知秘密；文档准确描述有限检测与源侧核对责任。
- 验收覆盖合成正反例、结构化和自由文本、编码/转义、非秘密决定保留及无敏感输出；具体实现写入 design 后再封口。

## D3：历史文件边界

- 根任务 D3 的实际答案为“core 与历史分离 (Recommended)”。core JSON、完整历史 JSONL 与 prompt 组成同一绑定包，标准库逐记录处理，增长索引放入临时磁盘；不新增 ijson，不兼容旧包。
- schema、整包 digest、核心/历史读取覆盖、所有权、receipt、校验、归档/恢复必须一起修订；核心必读、完整历史按需与秘密策略不变。实现验收覆盖全部调用链，不以拆文件或输出分页单独宣称内存问题已关闭。
- 这是设计决定，不是当前任务的实施批准。

## D4：检索分层

- 根任务 D4 实际答案：“保留原生受控策略 (Recommended)”。
- 修正代理一次后备与 CLI 内部受控尝试的层级；普通 search 使用 `--no-extra`，extra 依用户当前明确要求/批准启用。满足约束的 degraded 结果不后备，整条命令不可用后才允许一次自托管 Hikari；不改配置、凭据或增加第三入口。
- Grok 的顺序/并行、请求尝试总数/重试次数文档漂移与本项一起修订，实际内容回上游；Pennix 不直接修改其快照。

## D5/D6：真实源码任务与模型验收

- Grok 采用其源仓库最小任务文档，不初始化 Trellis；Windsurf 使用其已有 Trellis planning task。Pennix 通过 catalog 固定并生成上游快照。
- E01 实际答案：“当前 Codex 完整基线 (Recommended)”。12 Skill 各正、负、边界场景，共 36，加 8 组合，44 场景修订前后各一次；补两类真实原生交互门，总计至多 100 模型轮次、本机串行。不派发实现或 check worker，不扩大到远端与多宿主。
- 源侧保存可复现的无秘密输入、预期和净化矩阵，原始模型事件留临时目录；离线返回不是实际服务握手，无法运行的必要场景是 blocked，不用静态测试替代。

## D10：全部名称的简短职责规则

- 根任务真实自由答复要求全部 12 项统一 pennix- 前缀，名称尽量简短但正确描述职责，不强求动名词；之前 namespace-only 和全动名词草案停用。
- 当前 6 项新名：pennix-grok-search、pennix-siyuan-knowledge、pennix-component-lifecycle、pennix-tavily-search、pennix-windsurf-code-search、pennix-trellis-asset-check；其余 6 项保留。
- Grok/Windsurf 名称变更在真实源任务完成；CLI/package/component IDs 与运行态标识按各自职责保留，不全局替换或建立旧 Skill 别名。
- 全部真实 caller、catalog/command targets、bootstrap/模板、MCP helper 配置、根集成和模型前后 ID 必须一起纳入最终方案及验收。此为规划选择，未授权当前编辑源码或安装副本。
