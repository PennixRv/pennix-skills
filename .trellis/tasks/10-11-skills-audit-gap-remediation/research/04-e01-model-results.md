# E01 原生模型行为结果矩阵

## 冻结与执行边界

evaluations/skill-cases.json 已冻结 44 场景，SHA-256 为 f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1。输入和判断标准修订前后保持，旧/新身份映射明确；模型总轮次至多 100。驱动自身 5 项离线测试通过，CI 不运行付费模型。

当前 native codex-cli 0.162.1，调用没有 model/provider override；只匹配用户 config 的 model 和 reasoning 安全键得到当前配置选择 gpt-6.1-sol / xhigh。原生 --json 已观察事件不报告模型 ID，因此 actual_model 为 null，不能用模型自述补齐或把配置选择说成服务端返回身份。实际 turn.completed 用量与工具事件作为执行证据，结论限定本次原生 CLI/配置和真实能力，不推导全部平台。

原始 stdout JSONL/stderr、临时 fixture、限次记录均留 /tmp/pennix-skills-gap-e01-20261011/runs 的私有目录，不进入 Git。过程使用真正已暴露的原生 MCP、read-only sandbox/ephemeral 和原有 Hook 信任，不派发实现/check worker或绕过权限。涉及持久化/服务请求的场景只验证实际入口加载和停止边界，真实服务/原生交互门仍独立。

## 已人工核对

| 阶段/ID | 实际读取与动作 | 判断与限度 |
| --- | --- | --- |
| before S01-negative，第 1 次 | 实际加载 pennix-fastctx-routing；fastctx.inspect_local_file + fastctx.grep，对指定 fixture.txt 返回 1 条匹配、Complete；未网络或 shell 包装 | 本地负触发路径通过；input_tokens 65001、cached 46464、output 573。不是 Grok 正触发或 UI/嵌套证据 |

整组 before 已串行完成：36 个单 Skill 场景和 8 个组合场景均有固定摘要；C05（第 41 轮）为 `timeout/blocked_native_execution`，其余 43 轮为 `completed/review_needed`。摘要中的 review_needed 仍需按预期逐例人工核对，不能自动判为通过；C05 不重试，后基线仍按原 case ID 在最终活动集合运行，并把失败计入总预算。

前基线的能力观察显示，模型能按旧活动集合中的实际目录发现缺失路径并转到真实安装根；部分组合场景发生预期的工具失败或边界超时，均保留原生错误类别。由于 before 阶段读取的是改名前集合，不能用这些旧名称结果证明 N01 已关闭。后基线必须复核新 Skill 身份、两命令 PATH、FastCtx 直接/原生嵌套语义及相同停止边界；所有结果先人工审阅，再进入根侧验收矩阵。
