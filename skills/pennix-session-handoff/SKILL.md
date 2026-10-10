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

`evidence_paths` 必须是已存在的、项目相对的、非运行态文件。rollout 路径必须明确为绝对路径：不得扫描会话目录，也不得按修改时间选择文件。请求中不得放入凭据、原始工具输出、转录文本、缓存路径或临时状态。辅助程序把 rollout 当作流式 JSONL 源读取到捕获边界，只投影符合条件的公开用户或助手消息及工具元数据。源可以很大；不设置包文本、记录、候选或收据长度上限。它排除 reasoning、developer、system 消息、原始工具参数、原始工具输出和凭据。文件顺序是时间线顺序，记录时间戳只作辅助。较晚的明确用户修正与早期事件一起保留，不静默覆盖历史。

JSON 包是完整的规范资产。配对 Markdown prompt 是紧凑导航视图，保留生命周期指令、已核验事实、语义摘要、记忆引用和待处理工作，同时引用 core 中完整的 `conversation.timeline`、`conversation.candidates` 和 `conversation.coverage` 字段，不重复它们。接纳时必须完整阅读两个文件。

运行：

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" --project-root . \
  write --request <request.json> --explicit-user-request
```

`write` 只输出一个包 ID 和 JSON 路径。它使用固定 UTC 格式 `YYYYMMDDTHHMMSSffffffZ`，在以下路径下写入唯一的配对包：

```text
.trellis/session-handoffs/<handoff-id>/session-handoff.json
```

时间戳目录冲突时失败，不覆盖旧包。它记录任务快照、Git 历史、请求的证据路径以及 rollout 覆盖范围或候选投影；不上传 rollout 内容，也不调用外部模型。

以后只对明确路径执行只读检查：

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/handoff.py" \
  --project-root . validate --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

`validate` 返回 `ready` 只证明包结构有效。生命周期就绪还要求观察到源边界和规范 JSON 或 prompt 配对；包含任务的包还要求原生 Trellis quiesce 或 seal 收据。目标必须协调当前任务、Git、证据和 rollout；目标 attestation 不能绕过源门禁。本 Skill 不改变任务状态、不控制工作节点，也不复制凭据、缓存或运行台账。

新包使用 schema 9。schema 8 包和已有配对 prompt 只可读审查；`status` 返回 `historical`，所有生命周期、归属和保留写入都拒绝它。继续工作要从当前事实创建新包，不能改写历史包。

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

`admit` 的目标 attestation 始终按固定顺序累计：完整读取 JSON core、完整读取配对 prompt、运行 `$trellis-start`、协调当前事实。未完成的前缀只报告进度，不创建目标预约，也不标记消费；只有完整四步前缀才记录 `reconciled` 这一逻辑消费标记。相同目标可在中断后重试，其他目标不能消费。源仍 pending 时记录 `blocked`，保持可重试且不声明消费。`target_source` 必须精确等于当前 Trellis 直接 `session_source` 的 `session:<target-key>`；规范源、源 rollout ID 和 rollout 会话 ID 不能冒充目标身份。

接纳从不执行 `pending.next_action`，不启动任务，不改变任务指针，也不关闭任务。后续继续必须另行获得授权，先执行归属 `claim`，再依据当前任务分类和阶段使用 `$trellis-continue`。只读 `analysis_only` 研究保持 planning，不运行 `task.py start`；变更任务只有在当前原生 seal 和批准存在时才 start，已经运行的工作恢复已有检查点。完成任务按原生 Trellis `finish` 或 `archive` 使用精确任务路径，不制造会话指针。

协调接纳后，`retention archive` 在确认 core 可解析、prompt 可读后原子复制二者。重试归档是幂等的；失败归档仍可再次归档，不重复 intake。`restore`、`reopen` 和 `purge` 都要求同一交接 ID。 `purge` 只在归档核验后移除规范 core 和 prompt；不删除任务、rollout、会话、记忆、资源、watch、日志或远程数据。收据保留为审计证据。`status --handoff <core.json>` 用于查看选定生命周期模式是否 ready；渲染器拒绝 pending 高保证模式。

## 新会话收尾

目标会话中“关闭交接”只表示在继续工作前用当前 Trellis 事实协调捕获任务：

1. 核验精确包，并在收据不是 `ready` 时停止。
2. 在处理 pending next action 前完整读取 JSON core 和 `session-handoff-prompt.md`。
3. 运行 `$trellis-start`，将捕获任务、Git、证据和待处理动作与当前事实比较。用 `action_authorized=false` 记录累计 `admit` 进度；只有完整读取、启动和协调序列才算消费。
4. 如果任务已经实际完成，先按正常 `$trellis-finish-work` 流程完成并归档。
5. 如果任务未完成、已变化或被阻塞，不从快照关闭；记录当前处置，并且只有适合继续时使用 `$trellis-continue`。
6. 协调后停止。不要执行 pending next action，也不要在用户后续指令前开始新的实施。

不完整读取、超时、网络或模型中断、进程退出都不算消费。已有 `admitted` 收据时，相同目标恢复同一尝试；其他目标不能替换。成功接纳后，包保留归档独立于消费，可重试。会话内压缩和普通重启只恢复目标当前任务，不调用交接接纳；手动重新进入时，已完成的目标收据是幂等的。

交接包只是导航提示。`ready` 收据不证明任务完成，也不授权关闭当前无关任务。源 rollout 会话 ID 不绑定目标 Trellis 任务。

## 任务归属转移

包含任务时先渲染 prompt，再按以下顺序推进包生命周期和 Trellis 任务归属。这些编排命令调用项目原生 `.trellis/scripts/task.py ownership`；本 Skill 不直接修改任务指针：

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership quiesce --handoff <core.json> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership seal --handoff <core.json> --expected-generation <n> --explicit-user-request
```

归属是原生任务屏障；需要时本地 `finalize` 记录额外边界证据，证据缺失保持 pending。

新会话完成只读接纳且用户明确授权继续后，才可以 claim 并关闭归属：

```bash
python3 "$PENNIX_HANDOFF" --project-root . ownership claim --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership consume --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership archive --handoff <core.json> --expected-generation <n> --explicit-user-request
python3 "$PENNIX_HANDOFF" --project-root . ownership status --handoff <core.json>
```

目标必须有自己的直接 `session:<key>` 身份且没有当前任务；不继承源指针。`claim`、`consume` 和归属 `archive` 是分开的、按 generation 核验、可幂等恢复的状态。归属 archive 是本地收据，与复制不可变 core 或 prompt 的交接 retention archive 不同。任何一种操作都不执行 pending.next_action，不关闭 Trellis 任务，不写入未批准状态，也不删除会话、记忆、资源、watch、rollout 或日志。

需要新会话入口 prompt 时，在精确 `validate` 返回 `ready` 后执行一次：

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-session-handoff/scripts/render_handoff_prompt.py" \
  --project-root <absolute-project-root> \
  --handoff .trellis/session-handoffs/<handoff-id>/session-handoff.json
```

渲染器以原子方式创建同一时间戳目录下的 `session-handoff-prompt.md`。首次渲染只是源侧准备；源侧仍需执行 `prepare`、必要的归属 `quiesce/seal`、`finalize` 和适用的 `retire`。确认 `status --handoff <core.json>` 返回 `ready` 后可幂等重跑渲染器，并将其标准输出原样作为最终交付，让用户直接复制 `text` 块到新会话。不要在最终块后追加摘要、核验说明或命令。

生成的 prompt 指导新会话再次核验，使用正常 `$trellis-start`，协调捕获任务，并依据当前事实选择 `$trellis-finish-work` 或 `$trellis-continue`。任务和 next action 只是导航提示，不能覆盖当前用户指令、Trellis 事实、Issue 状态或 Git 状态。ready-only prompt 渲染完成后停止；不要运行 finish、archive 或其他会使收据失效的变更。后续会话必须先完成自身核验和正常 Trellis 启动检查。首次接管在协调后停止，不自动执行 pending action。
