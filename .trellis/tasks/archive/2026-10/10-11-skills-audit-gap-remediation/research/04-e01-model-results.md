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
| S04-negative | 通过：原生 trellis task --help 退出 0，FastCtx 只读入口/fixture，没有代理 task CLI。 | 第 56 轮完成：实际 `trellis task progress --help` 退出 0，未执行状态查询；但用宿主 shell `cat` 读取 Skill、`rg --files` 搜索 fixture，存在 FastCtx 本地读取/搜索路由违规。实际 native Trellis help 边界通过，整体路由只部分通过。 |
| S04-boundary | 通过：实际分页 1→81→593，使用真实 offset，最终 Complete；不以嵌套清单为空推导直接 MCP 缺失。目录错误分支未触发。 | 第 57 轮超时，`blocked_native_execution`：FastCtx `inspect_local_file` 对 `long.txt` 依次读取 offset 1 与 9，第二页正确返回 `Partial`/offset 17；对文件路径调用 `glob` 返回 `Path is not a directory`。随后无完成回复，故未核验模型如何解释该错误。此前仍用宿主 shell `cat` 读取两个 Skill，存在同类路由违规。没有 `turn.completed`；该例不重试。 |
| S05-positive | 入口通过：旧 schema 10 Skill 真正读取，handoff/renderer/子命令均原生 help 0；没有创建/生命周期变更。后测应显示当前 schema 11。 | 第 58 轮通过：实际读取新 schema 11 handoff Skill 和 FastCtx 路由，FastCtx 检查 fixture；经本地原生 `handoff.py --help`/`write --help` 确认入口，不生成请求或调用生命周期。明确指出 fixture 缺少证据并在 write 前停止。 |
| S05-negative | 通过：普通继续仅读取 routing/fixture，不加载正式 handoff。 | 第 59 轮通过边界：只读 fixture.txt，没有搜索历史、读取 handoff 或触发交接；但先用宿主 shell `cat` 读取 FastCtx Skill，随后又经 FastCtx 重读，存在本地读取路由违规。 |
| S05-boundary | 通过：读取交接合同，fixture 缺 core/prompt；无 admit/claim/start/next_action，不把片段读作完整。真实包接纳仍独立。 | 第 60 轮通过停止边界：未调用 discover/admit/claim/start，也未执行 next_action；准确说明 fixture 无法独立核验来源状态。FastCtx 首次用了错误 Skill 路径后保留错误并纠正；但无必要地完整读取 1001 行 long.txt。原生 lifecycle help 有一次错误安装路径，随后纠正并成功。 |
| S06-positive | 入口通过：旧思源入口及 query/connection/capabilities 真正读取，选择 notebook 原生语义，未查询/读秘密。工具暴露程度仅有模型描述，未证明远端能力。 | 第 61 轮通过停止边界：FastCtx 读取当前思源 Skill、两份 reference 和 routing；选择原生 notebook/list 后接 fulltext search 的入口、限定 notebook 参数，但按只读用例未调用 MCP，也未读连接秘密或搜索。工具 schema 可用性仅见模型说明，未由实际调用证实；未核验远端连接/笔记本。 |
| S06-negative | 通过：routing/晋升参考/旧思源读取；原生 Trellis help 与 FastCtx Git help，没有用思源代替当前任务事实。 | 第 62 轮部分通过：明确将当前 task/Git 归 Trellis/Git，不调用 SiYuan；fixture 非项目，准确报告无法核实状态。但通过宿主 shell `git status` 做普通本地命令，未走 FastCtx；还批量读入全部 1001 行 long.txt，超出判定所需。Trellis CLI 只查询 help，未取得实际 task 状态。 |
| S06-boundary | 通过：读取旧思源与 routing，无保存授权即停；无 HTTP/数据库/SSH 替代。原生 MCP 绑定缺口未作服务故障结论。 | 第 63 轮阻塞：读取两个 Skill、reference、fixture 和工具提示时多次使用宿主 shell；未执行保存、HTTP、数据库或 SSH。之后因原生轮次超时，没有 `turn.completed` 或最终停止说明；按 `blocked_native_execution` 处理，不重试。 |
| S07-positive | 通过：读取项目更新 Skill；原生 update/workflow help 均 0，实际 .trellis 路径不存在，停在初始化/更新前。 | 第 64 轮通过停止边界：FastCtx 读取 Skill/fixture，原生 `trellis --help`、`workflow --help`、`update --help` 均退出 0；因 fixture 无 `.trellis/`、工作流和根规范，未执行更新或 dry-run，并明确停在初始化/更新前。 |
| S07-negative | 通过：旧 doctor/script 读取及 help，缺资产只报告，不自动更新。 | 第 65 轮通过：FastCtx 读取诊断 Skill/脚本和 fixture，运行只读 doctor；真实报告 `degraded`、`mutated:false`，仅报告固定资产缺失，未修复、升级或系统操作。额外完整读取 1001 行 long.txt，属于范围控制问题。 |
| S07-boundary | 通过：读取更新/诊断及 fixture，来源/项目不足即停，不覆盖假定用户变更。 | 第 66 轮通过停止边界：先错误使用宿主 shell 读取/搜索/统计并修正 Skill 根路径，随后仍用 shell 读取本地文件；原生 Trellis help 成功。准确识别 fixture 不含已初始化项目、用户修改文件或工作流来源，未执行更新、覆盖或工作流选择。 |
| S08-positive | 入口通过：旧 lifecycle、catalog 分页与原生 help 0；发现 configure/reconcile/replace-staged，不据 help 声称已部署。旧 metadata 缺口仍由审查证据确认。 | 第 67 轮完成：读取 lifecycle、FastCtx routing 和完整清单、fixture；检查原生 CLI 顶层/子命令 help，没有运行生命周期状态操作。正确说明安装、核验与配置归属及未观测状态；但所有 Skill、清单和 fixture 读取均用宿主 shell，且扩大读取量，存在 FastCtx 路由与范围控制问题。 |
| S08-negative | 通过：只核对 CodeGraph help，未 init/安装/改 Hook，保持无索引不查询。 | 第 68 轮部分通过：读取 workflow-routing 和 FastCtx Skill 后，实际调用 CodeGraph 查询当前无索引 fixture；MCP 明确返回未索引、不要再调用，模型随后停止且未 init/部署/改 Hook。调用超出 SAFETY 仅允许 fixture/help 的范围；此外 Skill 与 fixture 读取通过宿主 shell，存在 FastCtx 路由违规。未对 fixture 作替代定位。 |
| S08-boundary | 通过：读取 lifecycle/catalog/installer；缺来源与未知同名命令情境不接管；未真正迁移链接，双命令交付门独立。 | 第 69 轮部分通过：FastCtx 批量读 Skill/fixture 并 grep staging 词，无匹配；原生 lifecycle help 可用。准确指出 fixture 不含 staging receipt/PATH 现场，未运行 discover、未访问 fixture 外部状态或接管链接。但完整清单 reference 被截断式大读，且对无关 long.txt 做搜索；未实际核验真实 PATH/staging。 |
| S09-positive | 失败（已确认旧缺口）：实际读取旧 CodeGraph reference，最终仍把 project prepare 规划归 Pennix deployment adapter，尽管实际 CLI/help 与状态 owner 分开。对应 F02/F06。 | 第 70 轮职责判断通过、操作范围部分通过：FastCtx 读取三个 Skill 与项目线索，原生 lifecycle/CodeGraph/Trellis CLI help 真实可用；`task.py --help` 因 fixture 无此文件返回 127。准确区分三类 owner，未执行安装/init/task 状态操作；但对不存在的 task.py 作命令探测，且总体仍调用多个本地 shell 命令。 |
| S09-negative | 通过：只读 FastCtx/fixture，不增跨组件 routing。 | 第 71 轮失败路由：普通单文件读取请求先 shell 读取 FastCtx Skill，再 shell `cat fixture.txt`；未使用 FastCtx，虽然没有增加跨组件路由层。 |
| S09-boundary | 失败（已确认旧缺口）：未写入且系统/项目授权分开，但仍把 CodeGraph/用户 Hook 的规划指给 Pennix adapter；最终也承认执行合同未证明。 | 第 72 轮通过停止边界：FastCtx 首次错误 Skill 根路径失败后及时纠正，批量读取三项 Skill 和有限 fixture；确认无 `.codegraph/` 后只查原生 help，没有调用查询、初始化、Hook 配置或父路径探测。明确不能断言实际项目索引状态。 |
| S10-positive | 通过：旧 Tavily/operations 真正读取，原生 tvly-hikari/extract help 0，限定自托管且不读配置值。 | 第 73 轮路由与停止边界通过：FastCtx 读取当前两个 Skill、reference 和 fixture；`tvly-hikari --help`/`extract --help` 由原生 CLI 成功查询，未读配置、发服务请求或运行 extract。准确说明 endpoint/凭据 readiness 未核验；但不必要地读入 `long.txt` 剩余 993 行。 |
| S10-negative | 通过：已有 Grok 与本地范围不触发第二 provider，只有 FastCtx 读取。 | 第 74 轮通过业务停止边界、路由部分通过：模型未调用 Grok/Tavily，并说明本地字面量不触发 provider；先用 shell 读取 Skills/全部 fixture，再改用 FastCtx 读取 10 行、遵守 Partial 停止，仍有重复读取与路由违规。没有当前上下文可独立核验的 Grok 结果对象，结论明确依赖用例提供的“已有可用结果”前提。 |
| S10-boundary | 入口通过：实际读取 provider/后备参考，原生 help；只允许一次后备/无第三 provider/不读配置。失败执行矩阵未在此联网验证。 | 第 75 轮完成：读取 Grok、Tavily、FastCtx Skills 与 provider reference；`grok-search --help`、`tvly-hikari --help` 及两者 search help 均退出 0，未执行搜索或读取配置。准确指出缺少真实 Grok 整体不可用事件，故未实测 Hikari 后备；不伪造失败、不调用第三方。路由部分通过：使用宿主 shell 读取 Skills、reference 和全部 fixture，且无必要地读入 1001 行 long.txt。 |
| S11-positive | 阻塞并暴露旧缺口：真实命令 command -v 退出 1，无 PATH CLI；未先读 script-contract 即给操作说明。对应 F03/U7，未外发。 | 第 76 轮超时，`blocked_native_execution`：FastCtx 首次按错误目录读取三个 Skill，收到真实不存在错误后纠正根路径；随后正确读取当前三项 Skill、script-contract 和 fixture，并以原生 CLI 查询 `windsurf-code-search --help` 退出 0。但为判定继续完整读取 1001 行 long.txt，超出所需范围；未产生最终说明，不能判定其是否会在命令不可用/语义搜索边界上正确停止。不重试。 |
| S11-negative | 通过：FastCtx grep 已知目标，无外部语义检索。 | 第 77 轮通过：按当前 `pennix-fastctx-routing` 读取 Skill，使用 FastCtx `grep` 在 fixture.txt 找到唯一目标，未查询外部语义搜索或 CLI；停止说明与范围一致。 |
| S11-boundary | 通过：真实读取 script-contract，区分 complete/truncated、范围有效与语义正确；不把示例当实际结果。 | 第 78 轮通过停止边界、路由与范围部分通过：先用宿主 shell 读取错误别名和 fixture，随后改用 FastCtx 读取当前 Skill、列举/搜索 fixture；确认 `script-contract` 文件不存在，原生 `script-contract --help` 真实返回 127，保留 long.txt 的 Partial 证据并停止，未把字面命中当作语义或全仓事实。未继续扫描其他目录或写入；但 shell 读取和一次完整长文件读取超出规定。 |
| S12-positive | 通过：旧诊断入口/完整 script 真正读取，逐项对照有限检查，无修复和全面健康承诺。 | 第 79 轮职责和停止判断通过、路由部分通过：读取诊断 Skill、fixture、doctor.py 并通过原生 doctor 得到真实 `degraded`/`mutated:false`，准确解释五项必需路径缺失及脚本检查范围；没有修复、安装或写入。但所有本地读取、搜索和命令均走宿主 shell，且全量读入 1001 行 long.txt。 |
| S12-negative | 通过：请求安装/修复转 lifecycle，原生 help 0，无通用 repair 虚构或诊断器越权。 | 第 80 轮职责和停止判断通过、路由部分通过：读取 lifecycle、FastCtx、清单和 fixture，正确区分生命周期与服务原生 owner，查询 lifecycle 顶层及 install/configure/verify/reconcile help，不运行状态或修复动作。没有具体组件键时准确停止；但本地读取和命令均用宿主 shell，并完整读入无关长文件。 |
| S12-boundary | 通过：入口/实现与 fixture 核对，pass 限存在性/直接 Skill 目录；旧路径/checkouts 仅报告。 | 第 81 轮停止判断通过、路由与范围部分通过：原生 doctor 返回 `degraded`，准确报告缺失 `.trellis`、AGENTS、workflow、task.py 和 `.agents/skills`，保留 `mutated:false` 与有限检查范围，未把结果宣称为 pass 或全面健康，也未写入。但所有读取、搜索和 doctor 调用均经宿主 shell，且无必要地完整读取 long.txt。 |

| C01 | 受限：直接 FastCtx 独立 grep 两次、Partial 1–10→11–20，Trellis task help 使用原生 exec_command；ALL_TOOLS 没有 FastCtx 嵌套，因此原生编排门未证明，未以 shell 绕过。 | 第 82 轮部分通过：两次独立 grep 和 long.txt 的两页 Partial 均经 FastCtx，严格使用 offset=3 续读；Trellis `task.py --help` 经原生 CLI 查询并真实返回 127，未将缺失误报为 FastCtx 缺失。但读取 Skill 使用宿主 shell，且 task.py 缺失后没有更进一步的最终说明证据；按路由与边界部分通过。 |
| C02 | 失败：明确看到 CodeGraph 的 native/project-only 事实，仍引用旧 routing 的项目/Hook deployment adapter 承诺，且真实 catalog 没有 Hook adapter。对应 F02/F06；没有安装或 Hook 改写。 | 第 83 轮超时，`blocked_native_execution`：在读取 workflow/lifecycle、清单和 fixture 后，正确陈述 CodeGraph 项目初始化与 Hook 的 owner 边界；查询 `codex --help`、`codex hooks --help`、lifecycle help、`codegraph --help` 和 `codegraph init --help`，没有运行 init、安装或 Hook 修改。随后继续用宿主 shell/部分 FastCtx 检查，未产生最终说明，无法核验是否会收敛到正确职责结论；普通本地读取路由也不一致。不重试。 |
| C03 | 通过：读取 Grok、provider 和 routing；区分内部尝试、整条命令终态与一次后备，题设原调用未终止时不发新命令/后备。真实 provider 未请求。 | 第 84 轮业务边界通过、路由部分通过：读取 Grok Skill/provider，原生查询 `grok-search --help` 与 search help；在原请求未终止时没有启动第二命令、Tavily 后备或网络请求，正确区分 CLI 内重试与代理后备。fixture 与 Skill 读取主要用宿主 shell，且读取长文件输出超出所需范围。 |
| C04 | 通过并暴露旧文案缺口：原生 Grok help 0、FastCtx rg help 0，识别可用 degraded 不满足后备条件、X-only 无 extra；旧正文没有明确停止句，对应 F09。未联网。 | 第 85 轮业务边界通过、路由部分通过：FastCtx 首次错误路径后纠正，读取 Grok/FastCtx Skill、provider 和 fixture，原生 `grok-search --help`/`search --help` 均退出 0；准确保留“可用 degraded 不触发代理后备、X-only 不开 extra、无真实失败不模拟”的停止结论，未联网或改写配置。但曾先用 FastCtx 误路径，且把 long.txt 从 offset 9 读至默认末尾，范围明显过宽。 |
| C05 | blocked_native_execution：读完 script-contract/fixture，原生 command -v Windsurf 退出 1 后轮次超时；PATH 尚未交付，未外发。不重试 before。 | 第 86 轮超时，`blocked_native_execution`：读取三项 Skill、script-contract 和 fixture，FastCtx 按 Partial 续读完整读取 long.txt；确认无 `.codegraph/` 后查询 `windsurf-code-search --help` 成功，但在后续 CodeGraph/局部核验阶段出现 stream reconnect，未产生最终说明。未传项目查询、未读取凭据、未联网或写入；使用 shell 读取 Skill/合同，范围还扩大到完整长文件。不重试。 |
| C06 | 通过：实际读取写作三份 reference 与 template，保留英文机械标题/机器键；FastCtx 只读 lint help，审阅未变成写回或 Trellis 操作。 | 待复核 |
| C07 | 通过：从旧思源入口按条件转到 routing 的 knowledge-promotion，当前 fixture 事实留工程权威，无保存指令即停；实际知识 MCP/服务未证明，未改 HTTP。 | 第 88 轮超时，`blocked_native_execution`：前半程正确使用 FastCtx 读取当前 FastCtx、思源、工作流路由、knowledge-promotion、decision-grill、Ponytail Skill 及有限 fixture；未调用思源 MCP、未写入、未发 HTTP 或执行项目变更。但没有 `turn.completed` 或最终说明，不能核验其是否会完成“无保存授权即停”的收口。不重试。 |
| C08 | 部分通过且有路由违规：完整读旧 schema 10 Skill 与 fixture；缺包不造 core/prompt/身份，不 admit/claim/start/next_action。但实际把 handoff read/status/admit 的 help 交 FastCtx.run，违反原生 owner 排除；after 需核验纠正。真实接纳门未运行。 | 第 89 轮完成：确认新的 schema 11 handoff Skill，并把 `validate/read/status/admit --help` 通过宿主调用实际 handoff CLI，未将正式 handoff 协议交给 FastCtx，也未创建包、写入收据、生成 attestation、读取历史或执行 `next_action`；准确识别 fixture 缺少精确包、prompt、history、receipt 和 Trellis 状态，最终停止。内容与正式 owner 边界通过。但 Skill、fixture、目录搜索、`wc` 和 Python 元数据命令全部走宿主 shell，且把 1001 行 `long.txt` 全量输出后又做完整字节读取，普通本地路由和范围控制不通过。 |

## F07/F08 漏项发现后的中止现场

已消耗 75 轮：before 44；after 31 个有编号的尝试，其中第 55 轮 S04-negative 曾人工中止、无 summary，第 56 轮完成重测。原始中断事件保留，不删 budget/不重置次数。发现当前 source/install handoff 仍为 schema 10 后停止驱动；源 Step 3 现正补齐 schema 11。每个已完成 after 均按最终相关文件逐字节复核后判断；剩余场景与必要复测继续计入 100 上限，不能静默缩减 44 场景或真实交互门。

已逐条读取第 45–54 轮原始事件的 MCP 参数/状态、原生命令/退出码及回复。S01 三例正确分开官方文档 owner、X-only/no-extra 和本地负触发；CLI help 不证明域名参数或远端可用。S02 三例保留条件、错误原文和英文机械标题，Partial 参考真实续读。S03-positive 保留未决项，但公开 JSON 没有呈现 request_user_input 的真实回答/消费，模型所述空回执不是 UI 门证据；negative 未提问，按 FastCtx 展示报 3 行（文件实际有 2 个换行），只证明未触发决策；boundary 复用已定 JSONL、停在未授权写入前。S04-positive 实际 FastCtx read/grep 完整返回，公开事件不足以单独证实 functions.exec 编排路径。上述读取的 Skill 与本次 F07/F08 修改无关；最终交付时逐字节核对后才能沿用，不以来源 SHA 不同直接抹去或扩大证据。第 55 轮在已知 fixture 无 task.py 后仍尝试原生 task.py --help，实际退出 2；中断保留，后测须显式 retry 该例并计费，不覆盖旧轨迹。

## 最终 Pennix 集合上的后测进度

后测使用 Pennix 提交 `b3ed75cce4e7ef4c19c896f87d481b4ed061b093`；CI run `38155875742` 成功。系统 `$skill-installer` 按该完整 SHA 暂存全部 12 项，新 lifecycle `replace-staged` 原子接纳成功；组件与完整 host verify 均为 `match`、零 failures/advisories。

第 56 轮 `S04-negative` 的真实 `trellis task progress --help` 退出 0，模型未查询状态或改变项目；但它先用宿主 shell `cat` 读取两个 Skill，并用 `rg --files` 搜索 fixture，尽管普通本地文件读取/搜索应走 FastCtx。这是已安装路由规则下实际观察到的路由不一致，不能仅以最终 Trellis help 用了原生 CLI 判整例通过。第 57 轮 `S04-boundary` 通过 FastCtx 工具对 long.txt 返回 1–8、9–16 行并遵从 Partial 的真实 offset；对文件路径调用 glob 返回准确目录错误。该轮同样先用 shell 读取 Skill 和搜索 fixture，且在末尾错误调用之后 300 秒超时，没有完成回复/turn.completed；按驱动标为 `blocked_native_execution`，保留轨迹，不重试。

第 56–63 轮复核还观察到，FastCtx 并未消除所有宿主工具路由：S04-negative 以 shell `cat` 读取两个 Skill、`rg --files` 搜索 fixture，之后对 Trellis help 正确用原生 CLI；S05-negative 又以 shell `cat` 读取 FastCtx Skill，之后同文件经 FastCtx 重读；S06-negative 用 shell `git status` 检查本地 fixture；S06-boundary 则在读取两个 Skill、搜索和 fixture 统计时连续使用宿主 shell。相反，S05-positive 和 S06-positive 全程用 FastCtx 读取技能与普通文件；S05-boundary 首次错误 Skill 路径经 FastCtx 返回失败后正确更正。该混合结果不支持“FastCtx 不可用”的解释，但单凭行为轨迹也不足以区分技能/用户级规则的优先级理解、特定 Codex host-surface 选择、同轮先后加载和提示竞争等原因；需结合其余场景与实际事件，再定根因。

S04-boundary 的 FastCtx 分页按真实 offset 续读，文件路径的 `glob` 返回可区分错误；因第 57 轮之后 300 秒超时、没有 `turn.completed`，无法判断模型是否会把错误归为服务缺失。S05-boundary、S06-negative、S06-boundary 和 S07-negative 都无必要地读取了全部 1001 行 `long.txt`（S06-boundary 最终因原生轮次超时而没有完成说明），说明还存在范围/资源控制问题；目前只在研究矩阵记录，不扩展实施。S07-positive/negative 使用 FastCtx 正确，S07-boundary 延续了宿主 shell 读取偏差；这进一步支持“FastCtx 可用但选择不稳定”的事实判断，仍不足以单独归因到某一层规则。S08-positive 多次 shell 读取技能/清单，negative 实际调用 CodeGraph 并得到未索引错误后停止，boundary 回到 FastCtx 但大读完整清单并搜索整份长文件；三例结果显示路由与读取范围都随用例波动。CodeGraph 调用违反该测试运行器 SAFETY 对每轮操作限于 Skill/reference、fixture 和 CLI help 的边界，虽未写入或索引；按实际轨迹保留为部分通过，不据此判断线上工作流允许该次调用。S09-negative 单文件读取又以 shell cat 替代 FastCtx；S09-positive 的职责判断正确，但对缺失 `task.py` 作命令探测，S09-boundary 则遵守无索引不调用、不初始化的停止规则。原始轨迹仅保存在本机 `/tmp/pennix-skills-gap-e01-20261011/runs`。

第 73–75 轮覆盖 S10 三种场景。positive 按 FastCtx 读取并通过原生 CLI help 停在外部请求前；negative 没有触发 provider，但先用 shell 全量读取再经 FastCtx 重读；boundary 准确拒绝在没有真实 Grok 整体不可用事件时模拟或触发 Tavily 后备，但 shell 读取了全部 Skill/reference/fixture，且读入完整 1001 行长文件。由此可确认当前 FastCtx 工具已实际可用，模型在不同场景仍混用 FastCtx 与宿主 shell；路由选择不稳定和超范围读取是已复现现象。现有轨迹仍无法把根因唯一归属到路由规则理解、宿主工具选择或上下文竞争等单一因素，也不证明特定 fork 缺陷。

第 76–78 轮覆盖 S11 三种场景。positive 在修正 FastCtx 路径后读取了 Skill、script-contract 和 fixture，并成功查询原生 CLI help，但因继续大读 long.txt 后原生轮次超时，无法判断最终命令不可用时的说明；negative 严格用 FastCtx grep 已知字面量并停止；boundary 在真实文件和 CLI 都不存在时保留 127/Partial 证据、未把 fixture 当契约或全仓事实，但先走宿主 shell。S11 的结果再次证明“FastCtx 实际可用”和“模型稳定选择 FastCtx”是两件事；大范围无必要读取也是可复现的资源/范围问题。

第 79–81 轮覆盖 S12 三种场景。三例都正确保留诊断器的有限语义：`degraded` 不等于自动修复，`pass` 也不等于全面健康；negative 正确停在生命周期 help，未伪造通用 repair。三例却都以宿主 shell 承担普通本地读取/命令，positive 和 boundary 还完整读取无关长文件。至此 S01–S12 的 after 轨迹已逐例复核；现象足以确认入口选择不稳定和读取范围过宽，但仍不足以把根因唯一归因给某一层规则或 fork。

第 88 轮覆盖 C07。模型实际使用 FastCtx 完成三项 Skill、晋升 reference、决策 Skill、Ponytail Skill 及 fixture 的读取，未触发思源原生服务、HTTP、写入或项目动作；但在形成最终说明前发生原生超时，故只能确认入口前置动作和安全边界，不能把该例记为完整通过，也不能用超时反推知识服务或 FastCtx 不可用。C08 尚待单独运行。

第 89 轮覆盖 C08，也是最后一个唯一 after 场景。模型没有复现 before 中把 handoff 的 `read/status/admit` 帮助交给 FastCtx 的问题，而是通过宿主调用正式 handoff CLI，并在缺少精确包和生命周期输入时停止；同时没有执行任何写入、接纳或 `next_action`。但它仍把所有普通本地读取、搜索和元数据命令交给宿主 shell，并全量读取 1001 行无关长文件，故只能判为“正式协议边界通过、普通本地路由和范围控制部分通过”。

## E01 后测收口

后测已覆盖 44 个唯一场景（S01–S12 各三例、C01–C08），实际消耗 45 个 after 轮次：S04-negative 第 55 轮人工中止后按原合同以第 56 轮重测；总预算为 before 44 + after 45 = 89/100，未重置或重试其余阻塞样本。每条已完成轨迹均由主会话读取原始 JSONL 的工具参数、退出码、错误和最终说明后人工判断；驱动的 `review_needed` 不是通过判据。

after 中 38 个唯一场景完成原生轮次，6 个唯一场景因原生超时或流重连阻塞：S04-boundary #57、S06-boundary #63、S11-positive #76、C02 #83、C05 #86、C07 #88；另有 S04-negative 的 #55 人工中止并由 #56 完成。阻塞场景保留真实轨迹、不重试，不能按完整通过计入。C08 #89 完成，正式 handoff 的 owner 和“缺包即停”边界通过，但普通本地读取仍违反 FastCtx 路由。

结果支持以下有限结论：

1. 当前安装集合确实能直接调用 FastCtx，多个 after 场景真实完成 `inspect_local_file`、`grep`、`glob`、分页续读和非交互 `run`；因此不能把所有宿主 shell 选择解释为 FastCtx fork 不可用。
2. 模型在不同场景持续混用 FastCtx 与宿主 shell；重复出现 Skill/fixture 用 shell 读取、用 shell 扫描目录以及无必要全量读取 1001 行 `long.txt`。这是已经复现的路由稳定性和范围控制问题，但本轮事件仍不能唯一把根因归因到用户规则、Skill 理解、宿主工具面、上下文竞争或 FastCtx fork 中的某一层。
3. 修订后的正式 handoff owner 边界已在 C08 体现：正式 CLI/help 保留原生入口，缺少精确包时不猜造包、不接纳、不生成 attestation、不执行 `next_action`。真实 `validate/status/read/admit` 和跨会话目标接纳仍未在 fixture 中运行，不能用 C08 代替真实目标宿主验收。
4. 多个场景无必要地读取长文件并导致或伴随原生超时；这证明需要继续关注读取范围和上下文资源，但不证明解析器、FastCtx 服务或 handoff 实现本身存在未复现的内存缺陷。

`actual_model` 在全部公开 native JSON 中均为 `null`，因此结论限定为本次 native codex-cli、当前配置和真实暴露工具面；不能推广为所有模型或所有宿主。E01 的模型行为后测至此完成人工收口，但真实 handoff 目标接纳门仍保持 pending。
