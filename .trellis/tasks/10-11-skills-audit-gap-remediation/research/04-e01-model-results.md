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
