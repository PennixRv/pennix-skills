# E01 原生模型行为结果矩阵

## 冻结与执行边界

执行期记录称 `evaluations/skill-cases.json` 的 44 场景 SHA-256 为 `f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1`。后续按文件与 Git blob 复核得到不同摘要 `0ce643aa95c7f530c2a5b2965975d56de77f9973dc865da848a21120d941d1db`，旧冻结字节目前无法复现，故不能证实 before/after 输入相同。总轮次上限仍为 100；驱动自身 5 项离线测试通过，CI 不运行付费模型。

当前 native codex-cli 0.162.1，调用没有 model/provider override；只匹配用户 config 的 model 和 reasoning 安全键得到当前配置选择 gpt-6.1-sol / xhigh。原生 --json 已观察事件不报告模型 ID，因此 actual_model 为 null，不能用模型自述补齐或把配置选择说成服务端返回身份。实际 turn.completed 用量与工具事件作为执行证据，结论限定本次原生 CLI/配置和真实能力，不推导全部平台。

原始 stdout JSONL/stderr、临时 fixture、限次记录均留 /tmp/pennix-skills-gap-e01-20261011/runs 的私有目录，不进入 Git。过程使用真正已暴露的原生 MCP、read-only sandbox/ephemeral 和原有 Hook 信任，不派发实现/check worker或绕过权限。涉及持久化/服务请求的场景只验证实际入口加载和停止边界，真实服务/原生交互门仍独立。

## 已人工核对

| 阶段/ID | 实际读取与动作 | 判断与限度 |
| --- | --- | --- |
| before S01-negative，第 1 次 | 实际加载 pennix-fastctx-routing；fastctx.inspect_local_file + fastctx.grep，对指定 fixture.txt 返回 1 条匹配、Complete；未网络或 shell 包装 | 本地负触发路径通过；input_tokens 65001、cached 46464、output 573。不是 Grok 正触发或 UI/嵌套证据 |

整组 before 已串行完成：36 个单 Skill 场景和 8 个组合场景均有固定摘要；C05（第 41 轮）为 `timeout/blocked_native_execution`，其余 43 轮为 `completed/review_needed`。摘要中的 review_needed 仍需按预期逐例人工核对，不能自动判为通过；C05 不重试。原计划要求在最终活动集合上复用同一 fixture 跑后基线，但当前因冻结字节摘要与私有预算不符而在第一轮前 blocked。

前基线摘要显示模型能按旧活动集合中的实际目录发现缺失路径并转到真实安装根；部分组合场景发生预期的工具失败或边界超时，均保留原生错误类别。由于 before 阶段读取的是改名前集合，不能用这些旧名称结果证明 N01 已关闭；且当前摘要无法替代 43 项逐例语义人工复核。恢复准确冻结文件或取得新的测试合同决定前，不运行也不宣称完成后基线比较。

## 最终来源复核与后测阻塞

后测启动前的来源核对发现本研究记录、私有 `budget.json` 和 44 份前测摘要所记 fixture SHA 为 `f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1`，但当前 `evaluations/skill-cases.json` 的文件与 Git blob SHA 均为 `0ce643aa95c7f530c2a5b2965975d56de77f9973dc865da848a21120d941d1db`。评估驱动校验源文件摘要与预算绑定后拒绝第一轮，状态输出为 blocked `ValueError`；budget 仍为 44 次 before、0 次 after，没有执行新的模型轮次。

当前仓库、`/tmp/pennix-skills-gap-e01-20261011/runs` 和任务落点未找到记录中摘要对应的旧 fixture 字节副本。不得修改预算摘要或把不同字节的前后数据标为同一测试。43 个 `review_needed` 的前测仍未逐例语义复核，C05 保持既有 `blocked_native_execution` 且不重试。因此 E01 的后测和前后比较为 blocked；需先恢复准确的冻结输入文件，或取得用户对新测试合同和剩余轮次安排的决定。

## 后测后的宿主状态

Pennix 最终提交 `43cdb51beba425631baad9214e94f186adcd8675` 的 CI run `38144053611` 成功，集合按该 SHA 原生重装。`verify --component pennix-skills --yes` 为 match、零 failures；`codex mcp list/get` 显示 SiYuan 已启用且 helper 字段存在并脱敏，但没有发起远端握手。完整 verify 仍被未知 lifecycle profile 摘要与 drifted 的用户级 AGENTS 文件阻塞；原生 reconcile/upgrade 按现有所有权规则拒绝修改，两项均保持原样。

## 冻结字节精确恢复

进一步有界复核发现，名称修订把 `skills_before` 中原应保留的 6 项历史 Skill 身份也全局改为新名。仅还原这些 before 字段，其余 44 场景 ID、kind、prompt、expected、skills_after、schema/预算和格式保持不动，文件精确 SHA-256 恢复为 f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1，与原 budget 及全部 before 摘要一致。原先“原冻结字节无法复现”的阻塞现已解除；这是已批准 N01/E01 的历史映射保真修正，不建立旧 Skill alias，不改变行为判断标准，不修改预算。原始 before 日志仍需逐例复核，C05 的历史 blocked 继续保留；接下来在最终新集合运行原计划 after。

## Before 逐例轨迹复核

下表由主会话逐条读取原始 item.completed 的 MCP 参数/状态、CLI 命令/退出码和最终说明后判断；不使用驱动的 review_needed 自评作为通过证据。通过仅指 SAFETY 限制下的入口、路由及停止行为，不证明远端服务、写入或完整交接。公开 JSON 未呈现的原生提问/嵌套调用不能用模型自述补证。after 正按相同输入和原预算串行运行，实际安装树为 b60a931；e263fda 只恢复 fixture/研究，不改变 Skill 树。

| ID | Before 观察与判断 | After |
| --- | --- | --- |
| S01-positive | 入口通过：真实读取旧 Grok、openai-docs、routing；原生 fetch/search help 均 0；识别官方文档 owner 优先，未联网。具体域名参数运行未验。 | 待复核 |
| S01-negative | 通过：FastCtx 读取 routing 并 grep 指定 fixture，1 条匹配，无网络。 | 待复核 |
| S01-boundary | 通过：读取 X reference，原生 search help 0；候选命令明确 source x/no-extra，未发 web/X 请求。 | 待复核 |
| S02-positive | 通过：读取写作入口、受控参考及 notes，保留失败条件和错误原文，无写入。 | 待复核 |
| S02-negative | 通过：仅读取 routing/notes，原文引用 FC_PATH_INVALID，未加载改写流程。 | 待复核 |
| S02-boundary | 通过：读取工作流载体参考及 template，保留英文机械标题与键，未写入。 | 待复核 |
| S03-positive | 受限：实际读取 grill；回复保留未决选择，未执行依赖。公开 JSON 未单独呈现 request_user_input 事件，回复所述空 answers 不能证明真实 UI 门。 | 待复核 |
| S03-negative | 通过：FastCtx 文本与 hex 核对 2 个换行，无决策提问。 | 待复核 |
| S03-boundary | 通过：读取 grill/写作及 fixture，沿用已定 JSONL，不重复提问，停在写回前。 | 待复核 |
| S04-positive | 通过：直接 FastCtx read/grep 指定 fixture，无 shell 替代；嵌套能力未证明。 | 待复核 |
| S04-negative | 通过：原生 trellis task --help 退出 0，FastCtx 只读入口/fixture，没有代理 task CLI。 | 待复核 |
| S04-boundary | 通过：实际分页 1→81→593，使用真实 offset，最终 Complete；不以嵌套清单为空推导直接 MCP 缺失。目录错误分支未触发。 | 待复核 |
| S05-positive | 入口通过：旧 schema 10 Skill 真正读取，handoff/renderer/子命令均原生 help 0；没有创建/生命周期变更。后测应显示当前 schema 11。 | 待复核 |
| S05-negative | 通过：普通继续仅读取 routing/fixture，不加载正式 handoff。 | 待复核 |
| S05-boundary | 通过：读取交接合同，fixture 缺 core/prompt；无 admit/claim/start/next_action，不把片段读作完整。真实包接纳仍独立。 | 待复核 |
| S06-positive | 入口通过：旧思源入口及 query/connection/capabilities 真正读取，选择 notebook 原生语义，未查询/读秘密。工具暴露程度仅有模型描述，未证明远端能力。 | 待复核 |
| S06-negative | 通过：routing/晋升参考/旧思源读取；原生 Trellis help 与 FastCtx Git help，没有用思源代替当前任务事实。 | 待复核 |
| S06-boundary | 通过：读取旧思源与 routing，无保存授权即停；无 HTTP/数据库/SSH 替代。原生 MCP 绑定缺口未作服务故障结论。 | 待复核 |
| S07-positive | 通过：读取项目更新 Skill；原生 update/workflow help 均 0，实际 .trellis 路径不存在，停在初始化/更新前。 | 待复核 |
| S07-negative | 通过：旧 doctor/script 读取及 help，缺资产只报告，不自动更新。 | 待复核 |
| S07-boundary | 通过：读取更新/诊断及 fixture，来源/项目不足即停，不覆盖假定用户变更。 | 待复核 |
| S08-positive | 入口通过：旧 lifecycle、catalog 分页与原生 help 0；发现 configure/reconcile/replace-staged，不据 help 声称已部署。旧 metadata 缺口仍由审查证据确认。 | 待复核 |
| S08-negative | 通过：只核对 CodeGraph help，未 init/安装/改 Hook，保持无索引不查询。 | 待复核 |
| S08-boundary | 通过：读取 lifecycle/catalog/installer；缺来源与未知同名命令情境不接管；未真正迁移链接，双命令交付门独立。 | 待复核 |
| S09-positive | 失败（已确认旧缺口）：实际读取旧 CodeGraph reference，最终仍把 project prepare 规划归 Pennix deployment adapter，尽管实际 CLI/help 与状态 owner 分开。对应 F02/F06。 | 待复核 |
| S09-negative | 通过：只读 FastCtx/fixture，不增跨组件 routing。 | 待复核 |
| S09-boundary | 失败（已确认旧缺口）：未写入且系统/项目授权分开，但仍把 CodeGraph/用户 Hook 的规划指给 Pennix adapter；最终也承认执行合同未证明。 | 待复核 |
| S10-positive | 通过：旧 Tavily/operations 真正读取，原生 tvly-hikari/extract help 0，限定自托管且不读配置值。 | 待复核 |
| S10-negative | 通过：已有 Grok 与本地范围不触发第二 provider，只有 FastCtx 读取。 | 待复核 |
| S10-boundary | 入口通过：实际读取 provider/后备参考，原生 help；只允许一次后备/无第三 provider/不读配置。失败执行矩阵未在此联网验证。 | 待复核 |
| S11-positive | 阻塞并暴露旧缺口：真实命令 command -v 退出 1，无 PATH CLI；未先读 script-contract 即给操作说明。对应 F03/U7，未外发。 | 待复核 |
| S11-negative | 通过：FastCtx grep 已知目标，无外部语义检索。 | 待复核 |
| S11-boundary | 通过：真实读取 script-contract，区分 complete/truncated、范围有效与语义正确；不把示例当实际结果。 | 待复核 |
| S12-positive | 通过：旧诊断入口/完整 script 真正读取，逐项对照有限检查，无修复和全面健康承诺。 | 待复核 |
| S12-negative | 通过：请求安装/修复转 lifecycle，原生 help 0，无通用 repair 虚构或诊断器越权。 | 待复核 |
| S12-boundary | 通过：入口/实现与 fixture 核对，pass 限存在性/直接 Skill 目录；旧路径/checkouts 仅报告。 | 待复核 |

| C01 | 受限：直接 FastCtx 独立 grep 两次、Partial 1–10→11–20，Trellis task help 使用原生 exec_command；ALL_TOOLS 没有 FastCtx 嵌套，因此原生编排门未证明，未以 shell 绕过。 | 待复核 |
| C02 | 失败：明确看到 CodeGraph 的 native/project-only 事实，仍引用旧 routing 的项目/Hook deployment adapter 承诺，且真实 catalog 没有 Hook adapter。对应 F02/F06；没有安装或 Hook 改写。 | 待复核 |
| C03 | 通过：读取 Grok、provider 和 routing；区分内部尝试、整条命令终态与一次后备，题设原调用未终止时不发新命令/后备。真实 provider 未请求。 | 待复核 |
| C04 | 通过并暴露旧文案缺口：原生 Grok help 0、FastCtx rg help 0，识别可用 degraded 不满足后备条件、X-only 无 extra；旧正文没有明确停止句，对应 F09。未联网。 | 待复核 |
| C05 | blocked_native_execution：读完 script-contract/fixture，原生 command -v Windsurf 退出 1 后轮次超时；PATH 尚未交付，未外发。不重试 before。 | 待复核 |
| C06 | 通过：实际读取写作三份 reference 与 template，保留英文机械标题/机器键；FastCtx 只读 lint help，审阅未变成写回或 Trellis 操作。 | 待复核 |
| C07 | 通过：从旧思源入口按条件转到 routing 的 knowledge-promotion，当前 fixture 事实留工程权威，无保存指令即停；实际知识 MCP/服务未证明，未改 HTTP。 | 待复核 |
| C08 | 部分通过且有路由违规：完整读旧 schema 10 Skill 与 fixture；缺包不造 core/prompt/身份，不 admit/claim/start/next_action。但实际把 handoff read/status/admit 的 help 交 FastCtx.run，违反原生 owner 排除；after 需核验纠正。真实接纳门未运行。 | 待复核 |

## F07/F08 漏项发现后的中止现场

已消耗 55 轮：before 44；after 10 completed，S04-negative 第 55 轮人工中止且没有 summary。原始中断事件保留，不删 budget/不重置次数。发现当前 source/install handoff 仍为 schema 10 后停止驱动；源 Step 3 现正补齐 schema 11。10 个已完成 after 的实际读取文件和上下文需逐例复核；只有最终相关文件逐字节不变且判断仍有效时才能沿用，不以旧来源摘要证明新 handoff。剩余场景与必要复测继续计入 100 上限，不能静默缩减 44 场景或真实交互门。

已逐条读取第 45–54 轮原始事件的 MCP 参数/状态、原生命令/退出码及回复。S01 三例正确分开官方文档 owner、X-only/no-extra 和本地负触发；CLI help 不证明域名参数或远端可用。S02 三例保留条件、错误原文和英文机械标题，Partial 参考真实续读。S03-positive 保留未决项，但公开 JSON 没有呈现 request_user_input 的真实回答/消费，模型所述空回执不是 UI 门证据；negative 未提问，按 FastCtx 展示报 3 行（文件实际有 2 个换行），只证明未触发决策；boundary 复用已定 JSONL、停在未授权写入前。S04-positive 实际 FastCtx read/grep 完整返回，公开事件不足以单独证实 functions.exec 编排路径。上述读取的 Skill 与本次 F07/F08 修改无关；最终交付时逐字节核对后才能沿用，不以来源 SHA 不同直接抹去或扩大证据。第 55 轮在已知 fixture 无 task.py 后仍尝试原生 task.py --help，实际退出 2；中断保留，后测须显式 retry 该例并计费，不覆盖旧轨迹。
