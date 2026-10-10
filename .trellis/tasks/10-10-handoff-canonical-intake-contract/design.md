# 交接规范与接纳设计

## 决策与目标

本设计承接 decisions.md 的 D1/D2 和 D3 最新纠正：核心必读、历史按需，保留一个 JSON 和配对 prompt，不维护旧全文阅读语义。修复落在现有三个脚本、Skill 与测试中，使用标准库，不增加附件、数据库、依赖或第二套消费台账。

## 规范数据

- 新写包使用 schema 10。`source.rollout` 只保留现有捕获身份字段：path、session_id、capture_end、record_count、parser_version。
- `conversation.candidates/timeline/coverage` 是完整合规投影的唯一规范位置。生成器复用已有 rollout_identity 投影，不把整份 rollout 再序列化到 source。
- timeline 继续保留 topic_key、state、event_index、repeat_count 和适用的 supersedes_event_index；正文及来源通过 event_index 引用对应 user candidate，删除完整 summary 和重复 source。引用不等于程序判断了真实决策或撤销含义。
- 候选顺序、公开消息全文、工具标识、来源位置、覆盖/排除/遗漏/未知记录继续保留。文本按现有规范化和脱敏规则投影；不声称保存原始转录字节，不裁切历史，也不纳入原始工具参数/输出、reasoning、developer、system 或凭据。
- 源侧沿用 semantic_capsule 字段并要求新包摘要非空，覆盖当前合同、重要决定/反转、现场、风险与开放工作。程序只验证存在和类型，语义充分性由源代理与目标当前事实核验负责。

## 校验与消费入口

沿用 handoff.py 的规范校验入口，生成后的 validate、只读 read、渲染器和生命周期均先通过它；渲染器复用当前版本常量，不另维护版本允许集合。

当前包校验覆盖所有实际消费结构：任务、Git、验证条目、conversation、各类候选、时间线引用和 coverage。检查字段类型及必需键、非布尔整数、递增唯一 event_index、引用对象和 supersedes 方向、来源位置与捕获边界、event_count 与候选数量、元数据集合及声明的一致性。按生产格式处理空记录、NUL padding、尾部 partial、未知类型、重复工具标识和不完整工具配对，不能假定它们是损坏或所有记录构成一对一分区。

错误使用已有 ContractError/PromptError 和结构化失败出口，避免 AttributeError/KeyError。校验全部投影记录，不采样或用包大小判断有效性；不新增源文件哈希真实性、现场 Git 不变或摘要语义完整性证明。

## 必读核心视图与分页

增加现有 helper 的只读 `read` 子命令，拟定接口如下；这些是待实现接口，不代表当前已有命令：

```text
read --handoff <core.json> --view core --offset 0 --length 4096
read --handoff <core.json> --view history --event-index <n> --offset 0 --length 4096
read --handoff <core.json> --view history --offset <n> --length 4096
```

- core 视图包含包身份、授权说明、完整任务/Git/事实/验证/证据入口、语义摘要及本地引用、全部 pending/阻塞/风险、捕获身份和覆盖概况。覆盖概况只给计数及按需引用，不嵌入全部候选、timeline 或 spans。
- history 视图无 event-index 时提供完整 conversation；指定 event-index 时提供精确候选含正文/来源。非法事件或分页参数受控拒绝，不猜最近事件。
- 视图从选定不可变 JSON 确定性生成 UTF-8 文本；每页返回实际 offset、next_offset、total_chars、complete 和原样 text。默认 4096 字符，采用 Python 字符位置，拼接完整页必须无损还原视图；输出边界不裁切规范资产。
- 代理逐页消费全部 core 到明确结束，再完整阅读配对 prompt；输出被宿主截断、缺页或中断时不得声明核心已读。read 不写消费状态、不自动 admit、不把页已生成当成代理已读。
- 历史按当前事实矛盾、重要决定/修正依据或用户要求查阅；摘要不能覆盖较晚用户指令和当前 Trellis/Git/证据。不能因历史非必读而省略真实矛盾的核查。

## 新声明与生命周期

- 当前 attestation 将 core_read 明确替换为 core_view_read，必经前缀为核心视图已读、prompt 已读、Trellis context 已建立、当前事实已协调。
- 增加 history_read（none/partial/full）及 history_refs。引用每项为 `{event_index: null|正整数, offset: 非负整数, next_offset: 更大的整数}`，与 read 的实际字符区间对应；相邻已读区间可合并，不要求逐页建立记录。none 要求空引用；partial 要求至少一个有效范围；full 要求完整 history 视图的区间覆盖从 0 到结束且无缺口，单条候选全文仍是部分历史。
- workflow_contracts 验证声明结构，handoff 使用同一视图函数验证事件存在、范围边界和 full 的覆盖。范围有效不证明文本确已被代理阅读。旧式字段、无效事件/范围或 full 覆盖不足受控拒绝。
- 生命周期只在既有本地 admit 收据中追加阅读范围/引用，不修改 core、不新建页游标台账；机器只验证声明结构与顺序，不能证明代理理解了文本。新声明依旧属于 coordinator asserted。
- 初次接纳只在源状态 ready、适用的原生归属 seal、真实当前 direct session 身份和完整必读前缀都满足后记录 reconciled。它不 start、claim、关闭任务或执行 pending；同目标恢复和幂等、其他目标不能替换继续有效。
- JSON/prompt 配对的原子保存、完整归属摘要、归档、恢复、重开和清理机制继续复用；不拆文件，所以不增加第三个文件的绑定或事务。

## 历史边界

schema 8/9 仅保留既有方式的只读格式检查和 historical 状态，已有配对 prompt 及收据原样保留。所有 lifecycle、ownership 和 retention 写操作仅允许 schema 10。不读取旧消费步骤来接纳、不迁移旧包，不实现旧全文阅读合同；对历史输入不宣称新阅读合同 ready。

## 修改与验收映射

| 文件或范围 | 改动 | 验收 |
| --- | --- | --- |
| scripts/handoff.py | schema、唯一投影、严格校验、read、接纳范围 | AC1–AC5 |
| scripts/workflow_contracts.py | 新 attestation 字段/范围/顺序校验 | AC3–AC5 |
| scripts/render_handoff_prompt.py | 共用版本/校验、核心阅读路径、历史按需 | AC1、AC3–AC5 |
| SKILL.md | 新请求/必读视图/声明示例和停止边界 | AC3–AC5 |
| tests/test_handoff.py、test_render_handoff_prompt.py | 当前格式、异常、分页和生命周期回归 | AC1–AC5 |
| 组件任务、必要的 backend 质量规格 | 实测合同及部署结果 | AC6 |

只更新实际存在的引用；搜索确认没有其他生产消费者，不新增无用途参考、界面文件或泛化框架。

## 交付、风险与回滚

组件沿现有非 PR main 交付，origin 为 PennixRv/pennix-skills。产品推送的精确提交即本次交付源；仓库没有独立版本包或标签发布流程，不新增发布机制。根任务拥有本机系统安装与组合验收的执行顺序。

规划基线 main 为 7d1211ae2f9788e2bdd30db7f073fa0c343a4d48；目前已安装产品为 d7bb1852a81bfd595631b96f39918fcb7468dd89，二者 skills 树相同。实施前重核 HEAD、远端、工作树及安装完整性；不以旧快照掩盖新漂移。

机器解析仍随完整投影大小增长；本次解决重复存储与接纳阅读成本，不承诺恒定内存。阅读和摘要语义仍由代理如实声明与核验。旧包只读是已定边界，旧包不能用新版继续写生命周期。

测试失败不发布；安装失败沿原生事务保留旧集合。必要回退通过明确本轮产品提交的 revert 和原生精确提交 staging 替换，保留历史记录与任务事实；不 reset、不覆盖未知漂移、不手改回执或安装副本。
