# Implementation Plan

## Preconditions

本任务、根任务、Windsurf 任务与 FastCtx 任务各自完成原生 seal 并一起展示；随后针对列明当前修订包的明确批准才可逐任务 native plan approve/start。Grok 采用 D5 源侧文档，其精确摘要绑定在根计划中。同一设计答复或只批准未列明源码任务的父任务不替代本门。主会话 inline，产品修改前加载 trellis-before-dev。

## Steps

1. 冻结 E01 输入、预期和能力矩阵；在未替换活动集合前完成 44 场景基线（单进程、本机、计入总 100 轮次）。记录实际模型/CLI/集合来源，原始事件流写临时目录。
2. 按 D1 查明全部 helper/import/CLI/文档/测试/根 caller，删除确认冗余部分，修正 owner 与 F01/F04/F10/E02 文案；落实 D10 精确名称和 N02 原生嵌套/静态共享数组分工、全部 catalog/bootstrap/CI/模板/消费者引用。源保留运行态 marker/CLI 等不同对象，无旧 Skill alias；根调用者由根任务修改。
3. 对 F07/F08 先写最小失败回归，再实现 schema 11 的 core/history 绑定、标准库逐记录读写与临时 SQLite 验证；修改 renderer、分页、history_refs、receipt、ownership 和 retention 全入口。
4. 落实 Windsurf catalog command mapping、Grok 旧 target 到新目录协调、Siyuan 已受管 MCP helper 引用更新，并扩展现有事务回退。 preflight/备份/写入/并发核验按 design，不重新索取秘密或接管用户配置；静态规则由 codex-agents 受管动作刷新。
5. Grok/Windsurf 源任务按各自计划修订并跑原生离线测试；提交推送后通过既有生成规则刷新快照。FastCtx 源 task 完成真实 0.2.24 发行后固定其 approved_version/来源；全部 catalog 指向验收 SHA/artifact，快照差异由固定来源重建。
6. 按现有 CI 方式运行全部 Python unittest，必要 compile/语法检查，Grok Node 与 Windsurf 源测试/pack 校验；审阅所有变更、调用者和安全错误输出。文案检查只处理实际修改文件，不递归历史任务。
7. 推送 Pennix 验收提交，根协调固定来源的 skill-installer staging → 新 lifecycle replace-staged → FastCtx 原生固定版本升级/apply → codex-config/agents 原生受管更新。若 workflow profile stale，先按 design 使用同一 lifecycle `reconcile`，确认摘要刷新或明确 blocked，再 discover/verify/PATH/receipt/实际字节检查；不调用 configure、不提示、不收集或输出凭据值。N02 两 owner 依赖顺序按 design，proof 不足即停，不手改配置。
8. 对最终活动集合执行同一 44 场景，完成两类真实交互门；更新源侧净化矩阵与根侧验收。必要失败复测计入剩余预算，超过 100 或能力缺失保持 blocked 并返回决策。
9. 更新影响到的原生规范与源侧执行记录，核对最终推送和消费者；根验收完成后归档/记录 session。收敛记录提交与代码交付提交区分，最终来源重新核对，不伪造完成。

## Validation Matrix

| 门 | 输入与执行 | 必须观察的结果 |
| --- | --- | --- |
| 严格整包 | 非法字段/类型、引用、顺序/计数、历史缺失/摘要变化、越界/链接、截断 JSONL | validate/read/render/status/ownership/retention 控制失败，无 mutation/secret/raw traceback |
| 资源 | 固定约 1 KiB 单记录，1k/10k/100k 规模；本机子进程内存限制 192 MiB，临时总数据上限 1 GiB；各操作串行 | writer/validator/core/history/event read/renderer/状态与范围验证/归档恢复全部通过最大规模；RSS 无随数量线性增长，完整记录计数/摘要不丢失 |
| 超长/故障 | 8 MiB Unicode 单条、半行/不完整记录、SQLite/磁盘/rename 故障、capture 边界 | 保真或明确失败，不能静默截断/ready 半包；证明 O(max record/core/page) 而非绝对常量 |
| 秘密 | 完全虚构的 key/token/xai/bearer/private-key、JSON 引号/转义/嵌套；正常技术文字 | history 仅敏感区间脱敏，非秘密上下文保留；request/core/receipt 命中拒绝；stdout/stderr/prompt 无合成秘密 |
| 读取/接纳 | Unicode 跨页、完整 core/prompt、history none/partial/full、缺页/越界/源 pending、无 task/有 task | actual ranges 精确，完整 prefix 才 reconciled；不 claim/start/执行 next action；native ownership digest 继续成立 |
| retention | 三文件完整 archive/restore、缺文件/改字节/重复目录/故障回退 | 原子整包操作，源不可改写，controlled failure |
| PATH | 新装、Grok-only 升级、重复替换、两命令链接冲突/遮蔽/权限/CODEX_HOME/第二链接失败 | verified prior proof 和新 desired map 分开；事务回退和精确卸载，无未知接管 |
| 身份/配置 | 12 名、真实上游、bootstrap/CI/模板/catalog；旧 MCP helper、Grok target、未配置/漂移/并发/写入失败 | 新目录与实际引用一致；不改凭据或无关字节，完整事务回退，静态资产原生更新与真实 MCP 核验 |
| 宿主接入 | N02 已知旧 static、新 policy、其他 namespace、两个 owner 更新顺序与故障 | 共享数组不再钉死，未知归属不覆盖；无 developer 指令/实验开关增量，实际新宿主 direct/嵌套/聚合/Partial 完整 |
| workflow profile | stale digest、current、未知/未就绪 target、非法字段/权限、写入失败、并发改写 | 仅安全 stale 更新 catalog digest 且保留 targets；其他漂移不变地 blocked，回滚不覆盖并发外部字节，重复调用幂等 |
| 组合/模型 | 根 D6 固定 44 场景前后与两类交互门 | 预期/动作逐例核验，正确 owner/资源/停止边界，失败不隐藏；至多 100 轮 |
| 安装 | 最终 SHA 全集合 staging 与新入口接纳 | 完整树、catalog、receipt、Grok/Windsurf PATH、configure owner 解析与原生 verify 一致 |

资源测试限制是本轮测试安全预算，不新建用户可配置资源平台；实际每个参数/返回结构以实施前重读接口为准，若无法满足已定门不可通过降低规模或换成样本冒充完成。

## Recovery

源码用精确提交审阅和正常反向提交回退，不 reset 既有无关工作。安装仅按受管原子事务恢复旧树/receipt/链接；真实漂移保留并停止。schema 11 失败不迁移/覆盖旧包，源 rollout 永远只读。执行事实进入本任务 research，不修改已封口三份计划的字节；实质变化 native replan。
