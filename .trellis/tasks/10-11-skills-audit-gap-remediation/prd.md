# Skills 审查缺口源码修订

## Goal

承接根任务 `codex-workflow-optimization/.trellis/tasks/10-11-pennix-skills-audit-gap-remediation/`，在本源码仓库收敛已确认归属 Pennix Skills 的审查缺口，并以可追溯提交和原生安装消费完成交付。当前仅规划，最终方案需原生封口和后续明确批准。

## Requirements

- R1：逐项承接 F01–F10 与 E01/E02 的本仓库责任，不复制根侧协调事实；F05 已有覆盖，保留其自然落点原则而不新建机制。
- R2：metadata、正文、reference、脚本、测试、catalog 和规范在本仓库真正来源修改；Grok/Windsurf 快照更新从真实上游发布来源物化，不直接修补快照。
- R3：Trellis 通用 runtime、任务状态、宿主交互、CodeGraph 项目初始化及 Hook 行为保留原生所有者。非职责 adapter 的保留、移交或删除由已定方案明确。
- R4：落实根 D2/D3：core JSON、完整历史 JSONL 与 prompt 统一绑定，标准库逐记录处理；秘密历史脱敏后继续，核心请求和收据拒绝命中；核心必读、历史按需且无旧包兼容。
- R5：复杂任务在批准前完成本仓库 PRD、design、implement 与必要证据；主会话 inline 实施，不提前编辑产品或测试。
- R6：按风险运行行为与组合检查，形成验收提交、推送 `origin/main`，由根任务协调完整集合 staging、原生 replace-staged、verify 和来源落点更新。
- R7：D7 用户新增 Windsurf PATH 命令，复用有限映射/receipt/transaction；有效旧交付核验与新期望映射分开，保留同名冲突与配置 owner 边界。
- R8：D6 以全部 12 Skill 的 44 场景前后模型轨迹及两类真实交互为门，总模型轮次至多 100、本机串行；源侧保存可复现输入、预期及净化结果，运行日志不入 Git。
- R9：落实根 D10：12 项全部 pennix- 前缀，短且职责准确，不强求动名词；采用 design 的 6 项新名，其余 6 项保留。Grok/Windsurf 在真实源改身份，全部 caller、catalog、配置、bootstrap/规则资产、安装和模型用例身份同步；不保留旧 Skill 别名。
- R10：落实 N02/D11/D12：允许 FastCtx 原生 MCP 嵌套并保留直接能力，普通操作范围与其他 owner 排除保持；停止静态模板对共享 direct-only namespace 数组的全量钉死。FastCtx 接入实现回真实 fork，Pennix 同步 route/static/catalog/受管升级与回退及 E01，不新增 developer 指令或手改配置。
- R11：落实根 D13：在 Pennix lifecycle 既有 reconcile 入口增加有界 profile catalog-digest refresh；只有严格受管 profile、有效的全部启用 target 和通过 readiness 的状态可更新，保留 target 选择与配置，拒绝未知漂移/权限异常/并发变更，原子写入并验证回退；不提示、不调用 configure/远端服务、不收集或输出凭据值。

## Acceptance Criteria

- [ ] AC1：本仓库所有承接项有明确处置、验证和与根任务的映射，不以 helper 测试替代公开入口验收。
- [ ] AC2：资源、秘密、provider 和职责合同与运行行为一致，负向/失败样本保留可复现证据。
- [ ] AC3：所有上游物化来源可核验，catalog 不维护第二张版本表，相关测试和差异检查通过。
- [ ] AC4：验收提交已推送，安装来源一致性和原生核验有根侧证据；无凭据、运行态或无关改动提交。
- [ ] AC5：两命令新装、有效旧集合升级、同名拒绝、第二链接失败回退和精确卸载通过；Windsurf 常规命令、owner 配置命令及集合收据不冲突。
- [ ] AC6：命名方案已定且全部受影响引用一致；如改名 Siyuan，受管 MCP helper 引用更新保留原连接和凭据、不接管用户配置，并通过失败回退与实际原生连接验收。
- [ ] AC7：共享 namespace 不再被本静态模板钉死整数组；合法其他 namespace 不误报 drift，旧有效静态配置可受管更新且不抢 FastCtx 的清理 ownership，调用域/聚合/分页通过真实组合门。
- [ ] AC8：profile reconcile 只更新 catalog digest 并保留 targets；未知/未就绪 targets、非法/不安全 profile、并发写入与写入失败有拒绝/回滚回归，current profile 幂等；实际完整 verify 结果单独记录。

## Notes

- 基线 `86a84211aea2df097e1826783c1a286d400405cd`，源码 `main`；当前分类为 planned/change_bearing，保持 planning。
- 跨仓库决策与交付总合同由根任务保存；本任务只保存本组件设计、实施、规范和验证。
