# 交接与资源生命周期收敛

## 目标与批准来源

承接根任务 `workflow-resource-lifecycle-convergence` 已接受合同的 W3：交接持久材料归位、无损 ZIP、原生透明历史读取与精确保留处置；保留接纳和 Task authority 边界。根合同位于父仓 `.trellis/tasks/in_progress/11-12-workflow-resource-lifecycle-convergence/` 的 `solution-design.md` 和 `implementation-contract.md`，联合接受修订为 `6b8d38953a76bf85650dc8b5a1af8f5f71002c91fa8a237d03b6af187c5b6453`。

用户在完整方案后明确指示“现在完整推进到任务停止点”；根 Task CLI 已记录合同接受和实施批准。本 owner 包承接该已有批准，不重问保留策略、历史压缩偏好或重复研究。根侧已完成需求和决策，owner 路线保留目标核对、设计、实施和交付审查，省略重复的决策空间阶段。

## 实施合同

1. 保留当前 schema 12 严格校验、接纳、连续性与原生 Task ownership CAS。历史只读、存储完整性和历史生命周期观察独立，不把旧 schema、旧 ownership 或过时任务状态重新解释为当前准入。
2. 新持久生命周期材料与交接包同目录；旧 runtime 材料由本 owner 按 ID 保真纳入。固定 `.runtime/handoff.lock` 提供短事务同步，不锁可移动 JSONL，不在 handoff 锁内调用 Task CLI 或等待 provider。
3. 标准库 ZIP 对全部原始成员按流复制、逐成员 SHA-256 校验并生成版本化 manifest；plain、ZIP 和已知旧 archive 均可通过逻辑 core 路径原生只读访问。保留原始 core、历史、prompt 与旧控制证据全部字节；缺失或未知成员明确诊断，不重写历史或伪造当前 schema。
4. 原生 retention 默认精确预览，ID 加当前 digest 才变更。archive 发布已校验 ZIP 后保留展开源；purge 单独确认，先在保留单元记录 intent，再切私有 tombstone，失败保持可恢复；restore 在私有目录完整校验和记录后原子发布。提交点、前缀一致性、并发复检和幂等恢复以根合同为准。
5. 补齐 Skill、渲染器、清理指引、测试和根侧调用者；保留 UTF-8 Unicode 分页、现有 192 MiB/100k/8 MiB 资源门，不新增依赖、数据库、资源注册表、守护进程或第二任务 authority。
6. 本包不执行真实交接创建、接管、pending next action 或历史删除。源码验收后由根侧固定提交、发布集合、原生更新安装，再按具体对象的新预览处理真实迁移或清理授权。

## 验收覆盖

| 接受条件 | 工作包 | Owner | 验证入口 | 交付证据 | 停止条件 |
| --- | --- | --- | --- | --- | --- |
| 当前准入与 Task authority 不回退 | W3 | handoff helper | 既有 CLI、生命周期、所有权回归 | execution.md | 接纳、身份、代次、源摘要围栏失败 |
| 历史全部原始字节可读、压缩和恢复 | W3 | handoff storage | plain/ZIP/legacy、成员 SHA、遍历及资源限制回归 | execution.md | 未知成员、路径、完整性或历史语义被错误提升 |
| 存储操作可精确确认、失败恢复 | W3 | handoff retention | 预览漂移、发布与删除故障注入、并发、恢复及重复执行 | execution.md | 旧摘要生效、唯一副本丢失、receipt 与提交点不一致 |
| 清理指引与调用者一致 | W3 | 本集合与根集成 | collection verify、文档/渲染/根 CLI 集成 | execution.md | 调用参数失配、语义路径失效或未运行必要门 |

## 回退与真实资产边界

源码回退只撤销本包改动；真实存储保持 owner 可恢复，不手改安装副本或 receipt。真实历史迁移、删除及用户内容变更须按根合同取得对应具体对象和影响的授权，整体源码实施批准不代替该授权。
