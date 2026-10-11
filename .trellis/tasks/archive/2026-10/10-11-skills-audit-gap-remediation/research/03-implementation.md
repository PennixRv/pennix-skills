# 源侧实施记录

## 授权与当前单元

完整修订包 revision 1 展示后获得用户明确实施批准；本任务 native plan approve/start 已成功，当前 in_progress，封口三份计划保持原字节。先完成 E01 冻结与前基线，不先替换活动安装集合。

本单元最小修改为 evaluations/skill-cases.json、run_codex_cases.py、test_run_codex_cases.py，以及 .github/workflows/verify.yml 的离线测试接入。真实 native Codex 保留当前模型和配置，串行只读、临时 fixture、私有原始日志、100 次总上限；驱动只输出净化动作候选，不自动宣称技能通过。不能安全执行或缺能力时 blocked，真实 UI/交接目标会话另验。

适用 backend quality/error 和共享思考指南已读取。活动安装树尚未改动；后续各单元完成即更新本自然落点，根只保存协调结果和来源。

## F01/F02/F04/F06/E02 与 N02 内容单元

lifecycle description 与入口正文补齐既有 discover/configure/reconcile/staging/seed 意图，明确系统部署和各组件原生项目初始化边界。workflow-routing 把 CodeGraph project prepare、Hook 实现还给原生 owner，移除对应 deployment adapter 承诺；Grok 普通搜索显式 no-extra，区分 CLI 自有有界尝试、代理不重复命令以及整个命令不可用时的一次 Hikari 后备。可用降级结果直接消费。

FastCtx 两个路由入口按 N02 允许实际暴露的宿主原生编排与直接调用，保留逐结果与 Complete/Partial、独立并行及依赖续页边界；没有扩大原生组件协议的可代理范围。移除“只承载一条 CLI”这一容易误读的措辞，仍只承载普通非交互命令，不把已有文件工具包装到 shell。

doctor 正文逐项对应当前脚本：pass 仅为固定路径存在及直接 Skill 目录有 SKILL.md；可选 checkout/包名、单一旧路径只是报告。它不证明 frontmatter、语义、版本、摘要、阶段或整体健康，未改脚本行为。两份已批准的长写作参考只添加按现有标题生成的目录，不改规则。

核对 lifecycle 主入口实际 imports、源码和根调用者后，删除没有公共调用职责的 codegraph.py、codex_hooks.py、trellis.py、前两者专属测试及未引用的 CodeGraph 参考。根唯一真实消费者是 run-workflow-integration.mjs 的两项固定测试入口，已同步移除；封口计划及历史任务证据保留。全体 Skill 改名、条件式 sibling 链接、catalog/模板/生成快照、暂存与私有 helper 升级、handoff schema 11 均尚未完成，不计为当前通过。

## 后续实施记录

E01 前基线已使用固定 fixture 串行完成 44 个逻辑轮次；S01–S04、S06–S12 及 C01–C04、C06–C08 均为 `completed/review_needed`，C05 在第 41 轮因原生命令执行边界超时而记录 `blocked_native_execution`，没有重试。摘要中的 `review_needed` 只表示需要人工对照动作轨迹，不能当作行为通过；原始 JSONL 仍只在本机 `/tmp/pennix-skills-gap-e01-20261011/runs` 保存。前基线读取的是旧活动集合身份，后基线必须安装最终新集合后按相同 44 个 case 运行；模型 ID 未由 native JSON 返回，继续记为 `actual_model: null`。

FastCtx 源侧已完成 0.2.24 接入修订的 all-features Rust 测试：217 个库测试、4 个 golden、15 个 CLI contract、1 个 v0.1.1 compatibility、1 个 glob、1 个 guarded burst、1 个 URI、6 个 property、13 个 runtime control center、8 个 server contract、11 个 shell contract、3 个 PDF 及其余 doc tests 均通过，1 个既有 ignored 测试保持 ignored。此结果仍未替代 clippy/MSRV/跨平台构建、发布和真实宿主接入门。

名称与 PATH 单元的首次回归发现受管命令实现仍只声明 Grok，且原子替换会遗留已证明链接指向旧目录；已补为有限的 Grok/Windsurf 双命令映射、旧 Grok receipt/旧 target 的证据约束重定向、现有链接重建和事务回滚，并增加旧 receipt 升级回归。修订后 lifecycle 组件测试 144 项通过。生命周期持久化状态目录、静态资产 marker、旧 receipt 路径和 CLI/package/component 标识按设计保持稳定，不因 Skill 目录改名被全局替换。

## Siyuan 受管 helper 迁移补齐

宿主首次安装后，`discover` 显示 Pennix 集合和 Grok/Windsurf PATH 已匹配，但 `siyuan-connection` 为 blocked：现有 MCP stanza 仍引用旧 `pennix-siyuan-memory` 路径。对照封口设计后确认这是源实现缺口：`replace-staged` 原先没有计划或事务化更新该 stanza。

现已在 `replace-staged` 预检阶段通过现有 SiYuan helper 读取并验证私有连接记录，仅识别带 Pennix 所有权标记、字段完全匹配且 helper 命令指向已知旧 Skill 路径的 stanza；只生成 helper 路径变更，不重新提示、不打印或改写令牌。未配置记录或没有受管 stanza 时不创建配置；私有记录无效、stanza 漂移或所有权不明时停止。集合替换事务现在将该配置写入和回读核验纳入现有树、receipt、命令链接事务；写入失败恢复旧值和旧集合，写入前并发变化停止，回滚时遇到第三方新字节则保留该字节并明确报告事务未能完整回滚。

新增迁移规划、未配置、不受管或漂移配置、正常原子更新、写入失败、写入后报错及并发编辑回归；并发改写会保留外部配置字节、恢复旧集合并报告未能完整回滚。定向 SiYuan/集合替换测试 40 项通过；全仓 17 个 Skill Python 测试模块共 234 项、evaluation 离线测试 5 项均通过，`git diff --check` 通过。修复提交 `43cdb51beba425631baad9214e94f186adcd8675` 已推送，GitHub Actions run `38144053611` 成功；按该 SHA 重新安装后，Pennix 集合、receipt、Grok/Windsurf 命令链接均 match，`siyuan-connection` 为 configured，Codex 原生 `mcp list/get` 确认已启用且 helper 字段脱敏存在。该证据证明本地托管状态一致，不代表 SiYuan 远端握手成功。

## 收敛阻塞复核

最终安装后 `verify --component pennix-skills --yes` 返回 match、零 failures。完整 verify 仍被旧 lifecycle profile 摘要和 `~/.codex/AGENTS.md` 未知漂移阻塞。按现有原生 reconcile 尝试状态核验，明确返回 `lifecycle profile has an unrelated catalog revision`，没有迁移或改写 profile；静态资产原生 upgrade 此前也拒绝覆盖 drifted 的 AGENTS 文件，没有写入。受管资产边界要求保留这两处现场。

后基线在启动前被评估驱动按合同拒绝：source 文件当前精确 SHA-256 和 Git blob 为 `0ce643aa95c7f530c2a5b2965975d56de77f9973dc865da848a21120d941d1db`，但本记录既有冻结值、私有 budget 与 44 份前测摘要均记为 `f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1`。`load_cases` 要求精确字节摘要与 budget 一致，因此 after 在第一轮前返回 blocked `ValueError`；budget 仍为 44 次 before、0 次 after，没有新模型轮次。当前仓库与任务落点未找到旧字节副本，不能重写 budget 或伪称对照有效。前测 43 份 `review_needed` 也尚未逐例语义复核；C05 原生执行超时保持不重试。后测和 E01 对照验收因此 blocked，须找回原冻结文件及其真实摘要，或由用户批准新的前后测合同/轮次安排后再继续。

## N03：profile 摘要刷新决策与规划

完整宿主 `verify` 的失败中，`pennix-workflow-state` stale 与 profile stale 同源：catalog 更新后 profile 保存的 catalog 摘要仍旧。当前 `reconcile` 只允许已知 Firecrawl 退役场景，因此拒绝本次 catalog 修订；拒绝本身保护了未审查的 profile 状态。若坚持完成原计划的完整宿主验收，需判断是否在本任务增加受限的 profile-only reconcile：仅在 profile 结构和私有权限有效、全部启用目标仍存在且当前 readiness 可验证、更新前字节未并发变化时，原子更新 catalog 摘要并回读；保留目标选择和密钥记录，对无效/禁用目标、未知字段漂移、权限异常或并发写入拒绝，并覆盖回滚测试。此为新行为，未包含在已封口实现中。

用户通过原生 grill 选择“纳入当前任务（推荐）”。根 D13 和本任务 decisions.md 已记录答复；两侧均已 native replan。计划限定为复用现有 reconcile、只更改摘要、启用 targets 的 readiness gate、保护并发字节及失败回滚，不提示、不调用 configure/远端服务、不收集或输出凭据值。接下来完成两侧计划修订和 native seal，向用户展示新增范围并取得明确实施批准前，不修改产品代码或测试。该项不能解除 E01 fixture 摘要不匹配或 `~/.codex/AGENTS.md` 未知 drift。

## Revision 2 实施与 N01 落点复核

用户已明确批准包含 N03 的完整 revision 2；两侧原生 approve/start 已通过。此次恢复最初误用 FastCtx 调用了 task.py，返回没有会话身份的降级结果；随后纠正为 Codex 原生 exec_command，current --json 确认两侧均有真实 session_source、正确任务绑定、in_progress，原生 start 均成功。未注入身份或手写 pointer；原先“身份缺失”的判断撤销。

N03 已在现有 reconcile 增加现行命名空间 profile-only 分支：严格字段和 schema 类型、私有目录/文件、安全路径及当前全部 selected ID；只 probe 默认和选定 targets，均 ready/configured 后只刷新 digest，保留 target 数组顺序。复用原子字节 writer，在临时文件写入前及原子替换前比较原字节；回读不符或写入失败时仅恢复本次字节，第三方内容保留并报告 rollback-incomplete。正常分支不调用 configure、提示或远端服务；现有 Firecrawl/legacy 迁移条件独立保留。Skill 操作说明与 backend quality-guidelines 已同步。

新增 9 项 N03 回归。首次测试暴露夹具共用 XDG 目录导致权限污染，已按用例隔离；补充临时写入期间并发变更及回读故障恢复。全仓 17 模块共 243 项与 evaluation 5 项通过。

AGENTS 阻塞进一步按真实源复核：现场 SHA-256 为 a126ddcab9cef58a2fdc70d827d079accf28df3f10ede25df3d5c40e80687a58，逐字节等于已发布 d7bb185 的旧完整模板；不是未知个人编辑。当前模板只把 lifecycle Skill 引用从旧名改为新名，原升级允许列表漏掉最近的已发布模板。按已批准 N01 的完整旧模板受管升级合同，补入该唯一已证实摘要，新增实际旧内容可升级、追加个人内容仍拒绝的回归，不改变未知内容拒绝策略。首次回归重建旧文案时误用 ASCII 分号，核对真实文件后改为中文分号；更新后 lifecycle 80 项通过。最终代码复核时保留 legacy Firecrawl 的既有目标路径语义，避免误把先复制后更新的 destination 改回 legacy source；最终定向检查、提交、安装与实际 verify 仍待完成。

修复提交 b60a9311ca6942b90998d75cd7735d16d3ab5405 已推送 origin/main，CI run 38147739493 成功；系统 skill-installer 按精确 SHA 安装全部 12 项到相邻 staging，暂存 lifecycle replace-staged 原子接纳成功。实际安装入口的 profile reconcile 返回 refreshed，原生 codex-agents upgrade 返回 changed；没有手改活动集合、profile 或 AGENTS。完整 host verify 正在运行，结果单独记录。

E01 冻结字节已精确恢复：仅把 skills_before 中被名称修订误改的历史身份还原，文件 SHA-256 恢复为原预算/全部 before 摘要的 f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1。prompt、expected、after 身份及 44 场景与 100 轮预算未改变，私有 budget 不改写；该修正落实原 N01/E01 历史映射保真合同，不新增旧名入口。后测将使用新安装集合继续；43 项 before 轨迹仍需逐例核验，不把冻结问题解除当作行为通过。

## F07/F08 实施漏项核对

逐项复核已批准 Steps/Validation Matrix 时确认，源与安装树 handoff.py 仍为 SCHEMA_VERSION=10，SKILL.md 仍描述历史嵌入 conversation；Step 3 的 schema 11、独立 history JSONL、流式索引及秘密边界尚未实施。既有提交/局部测试不能覆盖该漏项。已停止正在运行的 after 驱动并保留原始事件及已消耗预算；不能把当前集合称为完整最终树，既有 after 结果仅适用于其实际读取的内容。补齐范围已在 revision 2 明确批准，无须新增范围决策或修改封口计划。

下一有界单元只落实 F07/F08：修改 handoff writer/validator/read/lifecycle/ownership/retention、renderer、共享 workflow_contracts、对应测试与 Skill/源规范。复用标准库、现有原子发布和摘要；不改 Trellis runtime/身份，不迁移旧包，不修改源 rollout。先读完整接口及调用者，保留失败回归，再完成规模/秘密/事务门；最终重新交付安装后复测受影响场景，所有轮次仍计入原 100 上限。

宿主核验已完成：b60a931 安装入口的 full verify 返回 match，零 failures/advisories，profile match，两命令及规则资产 match；根 full-local 13/13 passed、零 blocked。这些门独立于尚未完成的 F07/F08 和 E01。

F07/F08 失败回归确认旧 writer 生成 schema 10 且缺 history 文件。当前已改为 schema 11 三文件合同，候选/时间线/覆盖/动态分类与工具引用逐记录写 JSONL；重复/主题/工具及验证索引在私有临时 SQLite，缓存 2 MiB、temp_store=FILE，不交付数据库。core 只存固定分类统计和完整摘要/捕获绑定。所有 read/render/lifecycle/ownership/retention 先核验历史的摘要与规范字节、字段/引用/计数；历史分页只读请求页，收据重复扫描不保留历史列表。旧 schemas 8/9/10 当前入口全部拒绝，普通工具只读审阅不受影响。

秘密检测按 decoded 字段/值和有限 token/xai/key/bearer/private-key 规则进行，历史只替换识别区间或值，request/core/receipt 命中拒绝。加入 quoted/escaped/nested JSON 与正常技术文字回归、畸形但摘要重算的历史跨入口拒绝、SQLite/目录发布/恢复故障回退。第一轮旧测试因 schema 断言及嵌入历史假设失败，已按新公开合同保留对应行为覆盖；当前完整 handoff suite 41 项（资源门默认跳过 1）通过。192 MiB 显式资源门首次因测试 runpy 未设置脚本 import 路径失败，属于测试驱动差异；修正等价原生脚本路径后按原 1k/10k/100k 与 8 MiB 输入重跑，没有降低规模或预算。资源结果及全仓/真实交互仍待完成，不称 F07/F08 已验收。

首轮显式资源门通过，56 个 native helper 子进程涵盖四种规模，1k/10k/100k 已记录 RSS 峰值约 34 MiB，8 MiB Unicode 单条最大 97,056 KiB；原始结果只留 /tmp。收敛前复核发现 purge 仍逐文件 unlink、空公开消息未计入覆盖，且资源门未直接调用 ownership、未测临时 SQLite 存在期间的磁盘峰值。新增两项回归先失败，随后将 purge 改为整包目录切换并在收据失败时恢复，空消息显式计数、覆盖总数严格相等、partial tail 后禁止源记录；所有增长分类都批量提交，内存不足和 renderer 的 SQLite/编码异常控制失败。有限 JSON 检测只对可能是 JSON 的字符串解析，减少收据重复扫描成本。更新后全仓测试通过；最终资源门正在按原规模和预算串行重跑，并补入 task-bearing ownership/core_digest 及每次操作的临时磁盘峰值采样。资源 fixture 的 task.py 明确是测试替身，不计为真实目标宿主门。

最终 F07/F08 验证已完成：19 个 Python 测试模块共 260 项通过，普通运行按设计跳过显式资源门；session-handoff Skill 的 quick_validate 和 `git diff --check` 通过。显式资源门在 1k、10k、100k 与 8 MiB Unicode 四种规模运行 64 个 native helper 操作，全部退出 0；每个进程受 192 MiB 地址空间限制，最高 RSS 97,032 KiB，测试目录临时数据峰值 773,293,099 字节，低于 1 GiB。100k receipt、task-bearing ownership/core_digest、分页、renderer、prepare/seal/admit/status、archive/purge/restore 均覆盖。根 full-local 再验 13/13 passed、零 failed/blocked。该资源结果来自隔离 fixture；真实 handoff 目标宿主仍未验收。

最终资源门现已通过：64 个操作全部退出 0，资源与规模数值见上。当前本地差异尚未提交或推送。接下来按精确 Pennix SHA 交付、CI、原生全集合 staging/接纳与完整宿主 verify；再继续原 100 轮预算的 after 场景及人工轨迹核对。预算保持 55/100，之前 10 个不依赖本次 handoff 文件的 after 轨迹只在已逐字节核对所读来源后保留，S04-negative 的中断轨迹不覆盖；新测试轮次还须重试该例。当前工具目录没有可启动第二 Codex 目标会话的原生能力，非交互 `codex exec` 不替代真实目标；正式 handoff 接纳门保持待验证，不宣称任务完成。

## E01 after 收口

最终 Pennix 提交 `b3ed75cce4e7ef4c19c896f87d481b4ed061b093` 已推送，CI run `38155875742` 成功；系统 `$skill-installer` 按精确 SHA 暂存 12 项，新的 `replace-staged` 原子接纳完成，组件级和完整 host verify 均为 `match`、零 failures/advisories。固定 fixture SHA `f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1` 与 before/budget 保持一致。

after 已覆盖 44 个唯一场景，实际使用 45 个轮次（S04-negative 第 55 轮人工中止后按原合同以第 56 轮重测），总预算消耗为 89/100。S04-boundary #57、S06-boundary #63、S11-positive #76、C02 #83、C05 #86、C07 #88 保留为 `blocked_native_execution`，均未重试；C08 #89 完成。每条完成轨迹均由主会话读取原始 JSONL 后人工判断，未把驱动的 `review_needed` 自评当作通过，未把阻塞轮次包装成成功。

after 证明当前已安装集合可以实际使用 FastCtx 的读取、搜索、分页和普通命令接口，故不能将模型混用宿主 shell 统一解释为 FastCtx fork 不可用。与此同时，多个场景仍以宿主 shell 读取 Skill、搜索 fixture、执行普通本地命令，且多次无必要地全量读取 1001 行 `long.txt`；这是复现的路由稳定性和范围控制问题，但现有事件不足以把根因唯一归属到用户规则、Skill 理解、宿主工具面、上下文竞争或 fork 缺陷中的单一层。该行为证据留在 E01 矩阵，不扩大本次已批准代码范围。

C08 还验证了 schema 11 的 handoff owner 边界：正式 `validate/read/status/admit` help 通过宿主调用 handoff CLI，fixture 缺少精确包、prompt、history、receipt 和 Trellis 状态时不猜造、不接纳、不生成 attestation、不执行 `next_action`。但 C08 的普通本地读取仍未使用 FastCtx，因此仅为正式协议边界通过；真实源侧 `validate/status/read`、跨会话目标 host 接纳和实际 Trellis 事实协调仍需真实目标会话完成。

E01 模型行为后测已完成矩阵人工收口；`actual_model` 仍为 `null`，结论只适用于本次 native codex-cli、当前配置和实际暴露工具。源 task 与根 task 保持 `in_progress`，不因模型后测结束而归档；下一独立门是使用真实源会话和真实目标宿主完成 handoff 包的最终验收，且不得执行包中的 `pending.next_action`。

## 真实源 handoff 包

使用真实源 session `codex_01a123bd-4342-7ed1-b857-4f40a7dea46c` 和固定 rollout 创建的临时包为 `/tmp/pennix-skills-gap-e01-20261011/handoff-project/.trellis/session-handoffs/20261011T182832238893Z/session-handoff.json`，配对 prompt 为同目录 `session-handoff-prompt.md`，历史为 `session-handoff-history.jsonl`。源侧 `validate` 返回 `ready`；`prepare(core_only)`、Trellis ownership `quiesce -> seal -> retire`、本地 `finalize` 完成，最终 lifecycle `status=ready`，ownership generation 3/status ready，source boundary sealed，target not_admitted。

已通过原生 `handoff read --view core` 从 offset 0 读到 `complete=true`，核心 2,980 字符；配对 prompt 97 行已完整读取。包明确保留 `action_authorized=false`、task `planning/analysis_only`、下一步哨兵和目标宿主阻塞；`MUST_NOT_EXECUTE_NEXT_ACTION` 文件不存在。当前环境没有启动另一个真实目标宿主的原生接口，因此没有执行 `admit`，没有读取目标侧 Trellis 事实，没有 claim/consume/archive，也没有执行 pending action。该包和运行态收据只在 `/tmp`，不提交 Git；真实目标会话必须使用包中的 prompt 在另一宿主继续，并在完整协调后停在可继续现场。
