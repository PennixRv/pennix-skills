# Design

## Scope

本方案承接根任务 D1–D12，只修订 Pennix 实际所有的 Skill 内容、helper、handoff、catalog/collection、受管静态资产与验证和必要项目规范。Grok/Windsurf 的物化内容从上游固定 SHA 生成，FastCtx 接入实现回真实 fork，不直接在快照或安装目录语义编辑。代码、测试、模板、安装树尚未修改。

## Decisions

| 项 | 选定行为 | 本仓库修改落点 | 关闭证据 |
| --- | --- | --- | --- |
| F01 | description 覆盖已声明部署、配置、协调和安装核验意图，保持排除项目初始化 | lifecycle SKILL、必要 UI 元数据 | metadata/正文/catalog 一致，模型正负触发 |
| F02/F06 | 原生 owner；清理确无公共职责的 CodeGraph/Hook/Trellis helper 及专属测试/误导参考 | routing/lifecycle SKILL、adapters、对应 tests/reference | 全部实际 caller 核对，主入口/目录边界回归；根调用者同步 |
| F03 | 导航/coverage 修订由 Windsurf 上游负责，生成固定来源快照 | catalog materialized_skills，原生生成结果 | 上游测试、打包白名单、SHA 与快照字节一致 |
| F04 | 限定固定存在性/Skill 目录/唯一旧路径/可选 checkout 清单 | workflow-doctor SKILL | 当前 script 输出逐项对应，模型不误判全面诊断 |
| F05 | 已有自然留痕覆盖，无新增机制 | 本任务研究/计划/执行与 Git | 保留撤销依据，不编造修复 |
| F07/F08 | 分离完整历史，值级有限秘密检测和历史脱敏 | handoff.py、workflow_contracts.py、render_handoff_prompt.py、两份 tests、SKILL、对应 spec | 整包绑定、严格验证、全调用链资源、安全与真实接纳 |
| F09 | 分层命令政策，CLI 受控尝试不授权代理重试；默认 search --no-extra | routing/Hikari；Grok 上游固定快照 | 主体、参考与代码事实一致；组合模型和离线失败矩阵 |
| F10 | 只在跨来源晋升时直达 routing owner reference | Siyuan SKILL | 相对路径存在、条件明确、内容不复制 |
| E02 | 两份长参考加目录 | pennix-chinese-tech-writing/references/controlled-technical-chinese.md 与 terminology-and-typography.md | 全部目录锚点有效，正文不丢失 |
| E01 | 有限可复现模型行为基线 | 源侧验证用例/最小驱动、任务结果矩阵 | 根 D6 44 场景前后及真实交互，必要受限项 blocked |
| U7 | Windsurf 受管 PATH 命令 | catalog、skills_install/lifecycle 相关入口/测试、集合 README/规范 | 新装/升级/冲突/回退/卸载、现场 PATH 与 receipt |
| N01 | 根 D10 已明确全部 12 项统一 pennix- 前缀、短而职责准确、不强求动名词；6 改/6 保留 | Skill 身份、真实 source snapshot、全部 caller/catalog/bootstrap/静态资产/安装及必要配置 | 名称、实际 source、MCP/command targets 与模型场景一致，受管更新/失败回退可核验 |
| N02 | 根 D11/D12：取消两处强制 direct-only、保留直接能力；本仓停止钉死共享数组，允许同一 MCP 原生嵌套 | FastCtx/routing SKILL、config.toml.install、codex_static 现有兼容路径/相关 tests、catalog | 合法 namespace 无 drift，旧 static 由现有受管路径接受；实际宿主工具/聚合/Partial 门，不增加 developer 指令 |

根 research/06-naming-and-coverage.md 保存当前有效 12 项短职责表；原 3 改/9 保留和全动名词草案停用。6 项新名为 pennix-grok-search、pennix-siyuan-knowledge、pennix-component-lifecycle、pennix-tavily-search、pennix-windsurf-code-search、pennix-trellis-asset-check，其余 6 项保留。Grok/Windsurf Skill 身份回真实源；CLI/package/component IDs 不改。当前 Siyuan helper_path 与 merged_config 校验使用旧 Skill 目录，rename 会影响受管 MCP helper 引用；生命周期 bootstrap、规则模板、catalog/command targets 与根集成调用也需全链路核验，不能只改目录或把运行态标识全局替换。

## Session Handoff Contract

当前 schema 从 10 升至 11；当前入口只处理新合同，不引入旧包迁移、全文接纳或双格式写入。历史旧文件可以由普通只读文件工具审阅，不能在新生命周期中写入或消费。

同一时间戳目录含 `session-handoff.json`、`session-handoff-history.jsonl`、`session-handoff-prompt.md`。core 保存任务/Git/事实/semantic capsule/pending 和固定大小历史描述；历史描述绑定固定兄弟文件名、SHA-256、字节数、Unicode 字符数、记录数、有限分类统计与源捕获边界。历史路径不接受绝对路径、越界、符号链接或外部别名。prompt 由 core/统计与 lifecycle 生成，沿现有配对验证；不能将 prompt digest 反向写进 immutable core 造成封口后变更或循环摘要。

历史 JSONL 按固定 typed records 保存现有 candidate/timeline/coverage/topic/tool 等增长数据；正文只存一次，引用使用明确候选/事件 ID。保留现有公开投影、来源顺序、用户修正、重复关联和覆盖语义；所有随历史增长的数组或索引均离开 core。先在私有临时目录用标准库逐记录生成及 SQLite 索引核验，再流式输出、计算摘要、写 core，原子发布唯一目录。不截断消息/历史，不扫描其他会话。

SQLite 仅是本次操作的临时磁盘索引，限制缓存并批量提交，保存 repeat/topic/工具 ID/范围关联等随数量增长的数据；不随包交付、不建立持久索引。当前已有分块摘要、copyfile、私有模式与 fsync/原子替换尽量复用。失败不留下可误判 ready 的半成品。

统一验证：严格字段/类型（整数拒绝 bool）、顺序、引用、计数、覆盖、工具关联、摘要/大小/字符数与捕获边界；畸形、缺失或改变的历史在 validate/read/render/ownership/lifecycle/retention 均封闭失败。Trellis 原生 ownership 继续接收 core_digest；core 绑定历史摘要，Pennix 每次依赖动作前核验整包，不能改写 task/pointer。

core view 保持确定性 JSON，history view 是已验证的规范 UTF-8 JSONL，event-index view 为单条完整候选。Unicode 字符分页只生成请求页，next_offset/total_chars 可复原视图；保持只读、无持久 cursor。history_refs 仍由现有 append-only receipt 保存实际阅读范围，full 要求整段覆盖；结构校验不代表语义阅读。receipt 全文件逐记录处理，不累积历史事件列表。admit 仍只在完整四步 prefix 后写 reconciled，初始接纳不 claim、不 start、不执行 next_action。

资源合同：内存随最大单记录、core/semantic capsule、请求页和固定解析/SQLite 缓冲增长，不随历史记录数线性增长；时间/临时磁盘可随历史规模增长。超长单值并不具有常量内存保证。逐调用记录规模/RSS/磁盘及退出状态，所有受限失败必须清楚且不静默降级。

## Secret Handling

从共享值级扫描修复 quoted JSON、转义与已知 token/xai/现有 key/bearer/private-key 检测；不用 json.dumps 整个对象作为唯一秘密检测。历史只替换实际检测区间，使用固定标记，保留事件和其他文本。字段/值与自由文本均有合成正反例，覆盖边界、嵌套、转义、Unicode、拒绝/脱敏和错误输出卫生。

摘要、事实、请求与 receipt 命中仍拒绝；不修改原始 rollout，不打印疑似值，不承诺识别任意未知秘密。保持源代理语义核对责任，实际泄露并未被本次规划证明。

## Managed Commands

追加 `windsurf-code-search` 命令：集合目标 `pennix-windsurf-code-search/bin/windsurf-code-search`，链接 `~/.local/bin/windsurf-code-search`；Grok 命令目标同步为 `pennix-grok-search/bin/grok-search`。复用原链接机制，不新增 wrapper/global npm/service。catalog 仍唯一声明有限映射，脚本拒绝任意映射；命令名称与 Skill 身份是不同对象。

验证当前私有 receipt 实际 map、树 digest 与每个现有链接，然后协调到新期望 map；新 map 不反向推翻有效旧 Grok-only receipt。缺失 Windsurf 链接在事务中建立，第二链接/receipt/tree 故障一起回退。没有旧 receipt command proof 的同名链接即使指向同一目标也拒绝接管。卸载只删已证明归属的链接。

PATH 遮蔽、无归属文件/错链接、目录模式与 CODEX_HOME 冲突均阻塞；不修改 Shell 启动文件。现场只在 PATH 真正解析受管命令时声明生效。Windsurf configure/readiness 继续从 receipted collection 找 owner executable，不信任随意的 PATH 同名程序。

## Name Change And Owned References

精确改名对为 grok-search → pennix-grok-search、pennix-siyuan-memory → pennix-siyuan-knowledge、pennix-workflow-lifecycle → pennix-component-lifecycle、tavily-hikari → pennix-tavily-search、windsurf-code-search → pennix-windsurf-code-search、workflow-doctor → pennix-trellis-asset-check。其他 6 项保留；全部有 pennix- 前缀。上游两项回真实源，CLI/package/component IDs 不改，旧 Skill 目录与别名不交付。

caller 核对覆盖 Skill/reference/UI、AGENTS/README、catalog 的配置 member/skills/source.paths/materialized.name/bootstrap/commands.target、seed-arch.sh 下载/原生安装提示、CI、全部直接 tests 和根集成入口。生命周期模板引用改名后，codex-agents 通过已有受管静态资产接口刷新用户 AGENTS；不把名称当作替换运行态目录/所有权 marker 的依据，不改无关用户规则或复制 Trellis 通用模板。根的原生任务、workflow 仍使用未改名的 pennix-decision-grill，不需修改 Trellis runtime。

现有安装接纳的 preflight 必须验证私有 receipt/tree 及旧 command targets、Siyuan 连接所有者记录、现有受管 MCP 段的 helper 路径/解释器/完整字节和私有权限；未知/手改/符号链接/并发差异都拒绝。从已验证旧映射更新 Grok 链接至新目录、新建 Windsurf 链接；Siyuan 只更新 helper 引用到 pennix-siyuan-knowledge/scripts/mcp_headers.py，保留服务器、notebook、令牌和无关配置字节，不再次调用收集秘密的 configure 流程。未配置 Siyuan 不新增配置。

复用并有限扩展 replace-staged 现有事务：在删除备份前完成树/receipt/链接和受管 MCP helper 引用一致性验证，任一失败恢复旧树、receipt、旧链接目标和已证明归属的旧 MCP 配置；预检查或并发冲突发生在写入前即停止。不新增通用迁移 registry、任意回调框架或第二配置 owner。静态用户规则由 codex-agents 的独立受管动作刷新，失败保留交付未完成并按实际证据恢复，不能手写 .codex/AGENTS。卸载只删除实际收据证明归属的当前链接。

新旧名称转换不改变 E01 场景 ID 或判断标准。实际测试覆盖 fresh/bootstrap、完整旧树升级、新树幂等、改过/不安全配置拒绝、Grok 旧 target 重定向、第二链接/receipt/MCP 写入与并发失败回退、未配置 Siyuan 保持未配置以及新旧入口引用一致。现场只在原生 MCP 与真实 helper 引用验证后声称连接正常，离线回归不冒充服务握手。

## Model Evaluation Artifacts

统一最小落点为 evaluations/skill-cases.json、evaluations/run_codex_cases.py、evaluations/test_run_codex_cases.py；实现期才创建。前者固定 44 场景 ID、无秘密输入、预期、旧/新 Skill 身份与实际能力；驱动只调用当前原生 Codex、串行处理有限场景并流式保留临时 JSONL，禁止 worker、自造工具协议或模型自验收。已有 CI 增加驱动自身的离线 unittest，不在 CI 运行付费模型或服务请求。

真实日志只留本机临时目录；净化结果进入本源任务 research 的场景矩阵，包含实际读取/动作/停止与人工判断，不只输出自评 JSON。44 前＋44 后＋两类实际交互及有限复测总轮次至多 100。原生能力无法安全限制或必需工具缺失即 blocked，不新增绕过路径。隔离正式交接项目根为 /tmp/pennix-skills-gap-e01-20261011/handoff-project，仅在后续完整方案批准后原生初始化；已存在但归属不明则停止。当前没有创建该项目或运行模型。

## FastCtx Host Coordination

config.toml.install 的 features 片段不再声明 mcp__fastctx direct-only 数组；该项的旧受管清理由真实 FastCtx apply 完成，不由 Pennix 删除共享数组或覆盖用户 namespace。codex_static 的新 expected 不管理这个键，额外合法 namespace 因此不能被判漂移。root 指令片段保持不新增 developer_instructions，不更换内置提示；原有原生协议排除保留。

现有 apply_config 对 seeded 才写，对 current/compatible 不写，对 drift 拒绝。已用现有纯函数和仅内存内的目标模板验证：去掉该 namespace 段后，旧有效 static、合法额外 namespace、空数组均为 compatible，新模板为 current；不需要为 N02 新增迁移路径或修改通用 list 比较。native codex-config 接受已兼容配置并更新其当前受管来源记录，FastCtx 自己在其原生事务移除旧 owned 元素。每个 owner 只核验自己的字段/记录，不把共享文件因合法其他 owner 修改造成的整体 hash 变化一律视为漂移；真正私有 receipt、受管字段、路径、权限、并发冲突继续停止，不相互代授删除权。N01 用户规则更新仍按该节原有受管合同，不能以本项兼容结果授权覆盖用户 AGENTS。

路由说明区分 operation owner 与 native MCP 的调用位置。宿主确实允许时，functions.exec 内直接调用同一 FastCtx MCP API 可以编排独立普通本地操作；不是用 exec_command/Python/rg 启动替代工具。未在嵌套域暴露不等于全局缺失，真实入口不可满足高优先级要求时如实 blocked；Partial 续页保留依赖顺序。更新已有文案而非复制第二份工具清单/规则。FastCtx catalog 固定真实 0.2.24 发行来源，不能凭本机配置宣称新宿主已暴露工具。

最小回归覆盖旧有效 static/额外 namespace/空数组的兼容接受、native 兼容动作不重写、新配置幂等及原有归属拒绝；FastCtx 真正删除/故障回退在其源侧测试。E01 单体边界与 C01 固定 N02 的直接/嵌套/真实调用及输出反例，保持 44 场景和 100 轮总预算。

## Validation And Delivery

复用全部直接 Python unittest 和当前 Node 测试；新增非平凡资源/安全/事务回归，不为单纯文案增机械镜像测试。模型前后用例预期先冻结，静态与行为证据分别记录，provider fixture 不称真实握手。

上游先提交推送固定 SHA，再按 `.github/workflows/sync-collection.yml` 的 archive/npm-pack 规则生成快照与更新 catalog；不编写第二套快照算法。Pennix 通过 Git 发布验收提交，无需 npm release。安装由系统 skill-installer 从最终固定 Pennix SHA 安装 catalog 全集合到相邻 staging，再由新 staging lifecycle replace-staged 原子接纳；discover/verify 和命令检查必须来自实际新树。任何来源/漂移/新权限问题停在有证据的断点，不手改安装树。

## Risks And Replan Triggers

历史分离是已批准的设计选择但仍是公开包合同变化，旧包不能用新入口继续；只读保存不迁移。秘密检测是有限启发式。真实模型有实际用量且只能为所选宿主/模型背书。若需要新依赖、改 Trellis runtime、增 provider/真实配置、移除无关资产或超过模型预算，记录 decision-needed 并按 native replan 重新决策。
