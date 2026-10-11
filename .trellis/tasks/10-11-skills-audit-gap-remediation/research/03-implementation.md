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
