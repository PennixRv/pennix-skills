---
name: pennix-session-handoff
description: 仅在用户明确要求正式跨会话交接时，创建、核验或渲染一个带时间戳、语义摘要和本地 rollout 投影的会话交接包。
---
# 会话交接
本 Skill 创建供新的 Codex 协调代理使用的导航包。它不是会话转录备份、任务数据库、检查点台账、原生会话恢复机制，也不是继续中断工具调用的机制。Trellis 仍是任务和生命周期状态的事实来源；新会话必须重新核验这些事实。
普通工作、重启、上下文压缩、等待、验收失败、服务商失败或传输句柄丢失都不使用本 Skill。这些事件本身不授权交接。

用户明确请求正式交接时，先完成并核验必须让下一会话看到的工作。在 `.trellis/session-handoffs/` 外准备一个小型请求 JSON。顶层字段必须是：

```json
{
  "session_label": "本会话的简短描述",
  "facts": ["由稳定项目来源核验的事实"],
  "evidence_paths": ["AGENTS.md", ".trellis/workflow.md"],
  "next_action": "新协调代理的下一步",
  "blockers": [],
  "risks": ["已知残余风险"],
  "validation": [{"command": "检查名称", "result": "结果"}],
  "memory_projection": {
    "semantic_capsule": "任务合同、现场、决策、反转、核验、经验、阻塞和开放工作",
    "local": [], "archive_refs": []
  },
  "rollout": {
    "path": "/absolute/path/to/the-current-codex-rollout.jsonl",
    "session_id": "可选的宿主会话 ID"
  }
}
```

`session_id` 是可选的宿主会话标识，只记录为 rollout 元数据，不参与目标身份核验。

`semantic_capsule` 必须非空，由源代理根据当前事实写明重要决策、用户修正、否定或撤销，以及未完成工作和风险。程序只校验结构，不证明摘要完整；源代理必须核对其语义，不能让目标通过穷尽历史重新推导当前合同。

`evidence_paths` 必须是已存在的、项目相对的、非运行态文件。rollout 路径必须明确为绝对路径：不得扫描会话目录，也不得按修改时间选择文件。请求中不得放入凭据、原始工具输出、转录文本、缓存路径或临时状态。辅助程序把 rollout 当作流式 JSONL 源读取到捕获边界，只投影符合条件的公开用户或助手消息及工具元数据。源可以很大；不设置包文本、记录、候选或收据长度上限。它排除 reasoning、developer、system 消息、原始工具参数和原始工具输出；历史中的已识别秘密只替换敏感区间，保留其他文本，请求/core/收据命中则拒绝。检测是有限规则，不能保证识别任意未知秘密。文件顺序是时间线顺序，记录时间戳只作辅助。较晚的明确用户修正与早期事件一起保留，不静默覆盖历史。

core JSON 与同目录 `session-handoff-history.jsonl` 共同组成规范资产。core 的 `history` 描述绑定固定文件名、SHA-256、字节数、Unicode 字符数、记录数、有限分类统计与捕获边界。候选、时间线、覆盖区间、分类计数和工具关联以 typed JSONL 记录保存；正文只存一次，时间线通过 `event_index` 引用候选。`source.rollout` 只保存来源标识与捕获边界。配对 Markdown prompt 保留生命周期指令、已核验事实、语义摘要、记忆引用和待处理工作。接纳必须完整阅读程序提供的核心视图与配对 prompt；历史按需阅读，并准确声明实际范围。

写入与整包核验逐记录处理；随历史增长的索引只保存在本次操作的私有临时 SQLite 中，操作后删除。内存随最大单记录、core、请求页及固定缓冲增长，不随历史记录数线性增长；超长单条消息仍需要相应内存。分页不建立持久 cursor；每个依赖入口先核验完整历史绑定，不把摘要或样本成功当作全量语义阅读。

运行：

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" --project-root . \
  write --request <request.json> --explicit-user-request
```

`write` 只输出一个包 ID 和 JSON 路径。它使用固定 UTC 格式 `YYYYMMDDTHHMMSSffffffZ`，在以下路径下写入唯一的配对包：

```text
.trellis/session-handoffs/<handoff-id>/session-handoff.json
.trellis/session-handoffs/<handoff-id>/session-handoff-history.jsonl
```

时间戳目录冲突时失败，不覆盖旧包。它记录任务快照、Git 历史、请求的证据路径以及 rollout 覆盖范围或候选投影；不上传 rollout 内容，也不调用外部模型。

以后只对明确路径执行只读检查：

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" \
  --project-root . validate --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

`validate` 返回 `ready` 只证明 core/history 结构与绑定有效。生命周期就绪还要求观察到源边界；接纳另行核验配对 prompt，包含任务的包还要求原生 Trellis quiesce 与 seal 收据及当前归属状态。目标必须协调当前任务、Git、证据和 rollout；目标 attestation 不能绕过源门禁。本 Skill 不直接改变任务状态、不控制工作节点，也不复制凭据、缓存或运行台账。

新包使用 schema 12。当前入口只接受该合同；旧包不迁移、不准入，也不使用旧版分页或生命周期语义。历史旧文件可用普通只读文件工具审阅；继续正式交接要从当前事实创建新三文件包。

## 必读核心与历史阅读

目标先确认精确包的 `validate` 和生命周期 `status` 均为 `ready`，再调用原生阅读接口。`PENNIX_HANDOFF` 的设置见下节：

```bash
python3 "$PENNIX_HANDOFF" --project-root . read --handoff <core.json> --view core --offset 0 --length 4096
python3 "$PENNIX_HANDOFF" --project-root . read --handoff <core.json> --view history --event-index <n> --offset 0 --length 4096
```

核心视图包含所有非历史字段及历史统计、引用。必须从 `offset=0` 开始，按返回的 `next_offset` 逐页读取，直到 `complete=true`，再完整阅读配对 prompt。`offset`、`next_offset` 和 `total_chars` 按 Unicode 字符计数；依次拼接每页 `text` 可恢复完整视图。宿主输出若截断、页缺失或读取中断，不能声明已完整阅读；减小 `length` 后补读缺失范围。接口只读，不自动记录消费或推进任务。

历史视图指定 `event_index` 时返回一条完整候选的确定性 JSON，不指定时返回规范历史 JSONL。事实冲突、关键反转或用户要求追溯依据时，按需阅读相应历史；程序完成结构校验不能算代理读过历史。保留现有公开消息投影和规范化，不裁掉长消息或较早事件；已识别秘密按值或敏感区间脱敏，其他上下文保留。

目标 attestation 使用以下字段；任务为空时使用 `task_disposition="none"` 和 `task_path=null`：

```json
{
  "target_source": "session:<当前直接会话标识>",
  "core_view_read": true, "prompt_read": true,
  "trellis_started": true, "facts_reconciled": true,
  "history_read": "none", "history_refs": [],
  "action_authorized": false, "task_disposition": "incomplete",
  "task_path": ".trellis/tasks/in_progress/<task>"
}
```

`history_read` 只能为 `none`、`partial` 或 `full`。`none` 必须对应空引用；`partial` 记录实际读到的范围，例如 `{"event_index":1,"offset":0,"next_offset":4096}`，整段历史视图使用 `event_index=null`。`full` 要求整段历史视图的引用覆盖从 0 到末尾且没有缺口；完整阅读一条候选仍只算 `partial`。范围按实际阅读结果填写，可以合并相邻范围；程序检查引用和边界，但不证明代理理解。旧字段 `core_read` 被拒绝。声明与引用仅保存于现有接纳收据，不建立第二份阅读台账。

当前 CR 状态由 source `prepare` 收据中的四个 `cr_*` 字段记录；目标会话在 `$trellis-start` 后重新读取并协调当前 CR。目标 attestation 只用 `facts_reconciled` 表示当前事实已完成对账，不重复记录 CR 状态。

## 生命周期收据与保留

不可变 core 不是消费状态数据库。单独的本地追加收据可以记录源收敛、目标协调和保留，位于 Git 外：

```text
.trellis/.runtime/handoff-lifecycle/<handoff-id>.jsonl
.trellis/.runtime/handoff-archive/<handoff-id>/
```

设置一次现有辅助程序路径：

```bash
PENNIX_HANDOFF="${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py"
```

以下命令只在用户明确要求正式交接时使用：

```bash
python3 "$PENNIX_HANDOFF" --project-root . prepare --handoff <core.json> --mode core_only
python3 "$PENNIX_HANDOFF" --project-root . seal --handoff <core.json> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . finalize --handoff <core.json> --observation <project-relative-proof.json>
python3 "$PENNIX_HANDOFF" --project-root . admit --handoff <core.json> --attestation <project-relative-attestation.json>
python3 "$PENNIX_HANDOFF" --project-root . retention archive --handoff <core.json> --confirm-handoff-id <handoff-id>
```

`PENNIX_HANDOFF` 是上文已设置的现有辅助程序路径。`prepare` 固定本地 `core_only` 模式和直接源会话。`finalize` 记录本地边界观察；追加收据只保留非秘密本地证据引用。

源侧唯一顺序是：

```text
write -> validate -> render -> prepare(core_only)
      -> 有任务：归属 quiesce -> 归属 seal
      -> 无任务：seal --explicit-user-request
      -> 按需 finalize 本地观察 -> status=ready -> 最终渲染 prompt
```

独立的 `seal` 仅用于无任务的已捕获边界；它要求同一规范源会话、配对 prompt，以及当前无任务、无陈旧指针、无错误或歧义的原生结果。它不创建任务，也不绕过任务归属。会话身份来自 Trellis 独立的 `session_source`，不是任务指针的 `source`。

对包含任务的包，接纳前必须完成源侧归属 `quiesce` 和 `seal`。缺失本地证据保持 `pending`。`admit` 还检查准备模式的当前源状态；有效目标 attestation 不能把 `pending` 源变成已协调接纳。源就绪与目标协调是两条独立收据轴。

`admit` 的目标 attestation 始终按固定顺序累计：完整读取核心视图、完整读取配对 prompt、完成 `$trellis-start` 所需上下文、协调当前事实。已有明确上下文时不重复启动检查。未完成的前缀只报告进度，不创建目标预约，也不标记消费；只有完整四步前缀才记录 `reconciled` 这一逻辑消费标记。相同目标可在中断后重试，其他目标不能消费。源仍 pending 时返回 `pending`，保持可重试且不声明消费。`target_source` 必须精确等于当前 Trellis 直接 `session_source` 的 `session:<target-key>`；规范源、源 rollout ID 和 rollout 会话 ID 不能冒充目标身份。

接纳从不执行 `pending.next_action`，不启动任务，不改变任务指针，也不关闭任务。后续继续必须另行获得授权，依次执行归属 `claim` 和 `consume`，再依据当前任务分类和阶段使用 `$trellis-continue`；两项归属操作不推进任务阶段。只读 `analysis_only` 研究保持 planning，不运行 `task.py start`；变更任务只有在当前阶段授权与接受门禁满足时才 start，已经运行的工作恢复已有检查点。任务关闭按 `$trellis-delivery-review-and-closeout` 核验后，通过原生 `complete` 或 `cancel` 使用当前精确任务路径；它们分别进入 `completed/YYYY-MM` 或 `cancelled`。`$trellis-finish-work` 只记录进展，不代替生命周期关闭，不制造会话指针。

协调接纳后，`retention archive` 核验整包与 prompt，再原子复制 core/history/prompt 三文件；恢复也按整包核验和目录事务进行。重试归档是幂等的；失败归档仍可再次归档，不重复 intake。`restore`、`reopen` 和 `purge` 都要求同一交接 ID。`purge` 在归档核验后通过目录切换移除规范三文件，收据写入失败时恢复原目录；发现未知资产则拒绝清理。它不删除任务、rollout、会话、记忆、资源、watch、日志或远程数据。收据按 JSONL 逐记录处理，保留为审计证据。`status --handoff <core.json>` 用于查看选定生命周期模式是否 ready；渲染器拒绝 pending 高保证模式。

## 新会话收尾

目标会话中“关闭交接”只表示在继续工作前用当前 Trellis 事实协调捕获任务：

1. 核验精确包，并在收据不是 `ready` 时停止。
2. 在处理 pending next action 前逐页完整读取核心视图和 `session-handoff-prompt.md`，历史按需阅读。
3. 按 `$trellis-start` 补齐缺失上下文，将捕获任务、Git、证据和待处理动作与当前事实比较。用 `action_authorized=false` 和真实的阅读范围记录累计 `admit` 进度；只有完整核心与 prompt 阅读、上下文初始化和协调序列才算消费。
4. 已经处于 completed／cancelled 的任务只核验当前事实，不重复关闭。仍非终态的任务，即使材料看似完成，也不由接纳授予关闭权；只有另有明确关闭授权、当前归属及原生收尾审查通过时，才独立执行 complete／cancel。接纳阶段停在用户约定位置。`$trellis-finish-work` 仅记录进展。
5. 如果任务未完成、已变化或被阻塞，不从快照关闭；记录当前处置，并且只有适合继续时使用 `$trellis-continue`。
6. 协调后停止。不要执行 pending next action，也不要在用户后续指令前开始新的实施。

不完整读取、超时、网络或模型中断、进程退出都不算消费。已有 `admitted` 收据时，相同目标恢复同一尝试；其他目标不能替换。成功接纳后，包保留归档独立于消费，可重试。会话内压缩和普通重启只恢复目标当前任务，不调用交接接纳；手动重新进入时，已完成的目标收据是幂等的。

交接包只是导航提示。`ready` 收据不证明任务完成，也不授权关闭当前无关任务。源 rollout 会话 ID 不绑定目标 Trellis 任务。

## 任务归属转移

包含任务时先渲染 prompt，再按以下顺序推进包生命周期和 Trellis 任务归属。适配器只调用项目原生 `.trellis/scripts/task.py continuity` 与 `task.py transfer`，不直接修改任务指针：

包内任务路径保留捕获时的原文。若该路径已随目录治理移动，适配器将原完整目录名交给 Trellis 原生名称解析；Trellis 仍须唯一定位，并核验任务 ID、包绑定、代次、直接身份和路线。原路径仍存在时保持精确路径查询；歧义、身份不符或缺失记录继续拒绝，不建立旧路径别名，不改写交接包或运行记录。

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership quiesce --handoff <core.json> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership seal --handoff <core.json> --expected-generation <n> --explicit-user-request
```

`quiesce`、`seal`、`retire` 按连续代数执行：没有归属记录时从 0 开始，依次写入 1、2、3；再次交接从当前记录代数开始，每一步递增。`quiesce` 将包中可用的来源投影摘要交给 Trellis，Trellis 重新计算当前投影并建立归属屏障；之后每一步都核对该实时投影和路线快照。来源事实发生变化时停止，必要时在转出前用 `release` 恢复来源归属并重新准备包。需要时本地 `finalize` 记录额外边界证据，证据缺失保持 pending。

来源尚未完成 `retire` 时，可以在来源会话用当前代数释放转移并恢复原任务指针：

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership release --handoff <core.json> --expected-generation <n> --explicit-user-request
```

新会话完成只读接纳且用户明确授权继续后，才可以 claim 并消费归属：

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership claim --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership consume --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership status --handoff <core.json>
```

目标必须有自己的直接 `session:<key>` 身份；Trellis `claim` 在授权后设置目标任务指针，之后 `consume` 用当前代次确认归属。目标不继承来源指针。来源转出前可用 `ownership release` 解除屏障；稳定的 `claimed` 状态可在用户明确授权和当前代次校验后重新指定目标，进行中的 `claiming` 或 `recovery_required` 则由已记录的操作会话恢复。任务归属的 `claim` 与 `consume` 和包的 `retention archive` 是彼此独立的操作。目标会话消费归属后，handoff lifecycle status 仍按包收据与来源边界判断，不把归属状态当作任务阶段。任何一种操作都不执行 pending.next_action，不关闭 Trellis 任务，不写入未批准状态，也不删除会话、记忆、资源、watch、rollout 或日志。

若 `ownership status` 返回 `claimed`，但 `target_session_id` 与当前直接会话不同，且用户明确授权当前会话接管，可用状态返回的当前代次再次执行 `ownership claim`；Trellis 会将归属目标改为当前会话、递增代次并更新任务指针。随后用 `claim` 返回的代次执行 `consume`；消费前的任务写入仍会被拒绝。若当前会话已是记录目标，直接按当前代次执行 `consume`。进行中的 `claiming` 或 `recovery_required` 仍由对应操作已记录的会话恢复，不以超时自动接管。该恢复只重新指定 Trellis 任务归属，不重新接纳或改写 handoff lifecycle，也不改变 `retention archive`。

若来源已 `sealed`，但原会话未执行 `retire`，目标不得冒充来源，也不需要先 `start` 才取得身份。`task.py current --json` 在没有任务指针时也应返回真实 `session_source`；不支持该合同的旧项目先通过 Trellis 原生更新入口修复。

用户明确授权当前会话接管后，先通过只读原生入口取得并核对当前投影；该入口不设置任务指针：

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership status --handoff <core.json> --include-current
```

完整核对返回的 `current_projection` 中任务、阶段、证据及 Git 事实后，才把 `current_continuity_digest` 明确传给恢复命令。摘要不能自动视为已核对，也不能用旧包摘要替代当前摘要：

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership claim --handoff <core.json> --expected-generation <n> --expected-continuity-digest <已核对的当前摘要> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership consume --handoff <core.json> --expected-generation <claim返回的代次> --explicit-user-request
```

Trellis 保留不可变的来源 `continuity_digest`，只将已核对现场记为 `target_continuity_digest`，并在同一归属锁内清除仍匹配的来源指针、设置并核验目标指针。包绑定、当前代次、直接目标身份及原路线不匹配均拒绝。中断后的 `claiming` 或目标侧 `recovery_required` 只能由记录目标用当前代次重试，成功恢复不再递增代次；`retiring` 或来源侧 `recovery_required` 同理由记录来源恢复。

`consume` 成功后，任务归属转移完成；目标会话的普通任务修改、提交、阶段推进和交付收尾不再更新 handoff ownership generation，也不重新协调或改写原交接包。需要查看当前任务投影时只调用 `ownership status --include-current`；它是只读查询。若在 `claim` 前发现当前投影发生变化，回到上面的显式摘要核对和 `claim --expected-continuity-digest` 恢复路径，不为普通工作增加 post-consume 同步入口。

用户再次明确要求跨会话交接同一任务时，由当前 owner 准备一个新包。先按任务只读查询当前归属，再将观察到的代数交给新包的 `quiesce`；不要把旧包的记录缺失或不匹配视为代数 0：

```bash
python3 .trellis/scripts/task.py transfer status --task-id <当前任务ID> --task-path <当前任务路径> --include-current
python3 "$PENNIX_HANDOFF" --project-root . ownership quiesce --handoff <新core.json> --expected-generation <当前代数> --explicit-user-request
```

只有已消费目标的直接会话且任务指针仍匹配，才能用新包建立下一次转移；后续仍按 `seal`、`retire`、`claim`、`consume` 顺序推进。原交接包及其生命周期收据保留原样，不重新接纳，也不承担新转移的状态。

旧 Trellis 不支持上述 claim 恢复参数时如实停止并更新，不直接修改 `.trellis/.runtime/`，也不以接纳、归档或 `ready` 状态代替任务归属转移。

Trellis 的只读 `continuity show` 用于记录 CR 观察状态和当前投影摘要；适配器不调用 `continuity capture`。首次 `prepare` 收据保留 `cr_status`、`cr_source_digest`、`cr_observed_at` 和 `cr_observation_state`。CR 缺失、过期、被拒绝读取或 CLI 不可用都按实际状态记录，不改变包自身的结构核验结果。任务归属仍由 Trellis 在 `quiesce` 时重新计算当前投影并建立围栏；CR 无法提供投影摘要时，只有 Trellis 能独立计算当前投影才可继续该操作。包状态 `ready` 不代表 CR 新鲜、任务可继续或用户已授权。

需要新会话入口 prompt 时，在精确 `validate` 返回 `ready` 后执行一次：

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root> \
  --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

渲染器以原子方式创建同一时间戳目录下的 `session-handoff-prompt.md`。首次渲染只是源侧准备；源侧仍需执行 `prepare`、必要的归属 `quiesce/seal`、`finalize` 和适用的 `retire`。确认 `status --handoff <core.json>` 返回 `ready` 后可幂等重跑渲染器，并将其标准输出原样作为最终交付，让用户直接复制 `text` 块到新会话。不要在最终块后追加摘要、核验说明或命令。

生成的 prompt 指导新会话再次核验，使用正常 `$trellis-start`，协调捕获任务，并依据当前事实选择交付审查或 `$trellis-continue`；`$trellis-finish-work` 记录进展。任务和 next action 只是导航提示，不能覆盖当前用户指令、Trellis 事实、Issue 状态或 Git 状态。ready-only prompt 渲染完成后停止；不要运行 complete、cancel 或其他会使收据失效的变更。后续会话必须先完成自身核验和正常 Trellis 启动检查。首次接管在协调后停止，不自动执行 pending action。
