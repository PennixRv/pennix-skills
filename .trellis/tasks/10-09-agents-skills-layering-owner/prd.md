# AGENTS 分层与 Skills 审查问题修复

## Goal

承接根任务10-09-agents-skills-layering-remediation：SAG-01/02全局/03/04/07/08/09/10，规划全局静态资产分层、格式门禁、诊断、恢复合同与验证，不实施。

## Requirements

- Owner：本 Pennix-skills 源码仓库，`main`；基线 `cd2419f90aa85dd2d2c000cefd1aa251b098eb79`。根协调任务：`/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-09-agents-skills-layering-remediation`。
- 承接 SAG-01/02全局/03/04/07/08/09/10；仅修改本集合的静态资产、adapter、相关 Skill/reference、测试与维护合同。
- 用户D2/D3实际选择：用户AGENTS整份内容回lifecycle源码模板维护，无个人扩展区；个人规则也回模板。精炼完整准则和短索引，组件步骤渐进披露，项目状态合同归已选workflow。
- `codex-agents` 保持既有显式独立资产入口；普通 Skill 激活与其他组件部署不顺带写 AGENTS。
- 准确 YAML 解析需 PyYAML；本机已具备 6.0.3。声明解析能力依赖并对缺失报告清晰 capability gap，不写自制 YAML 子集解析器、不自动 pip 安装、不以 regex fallback 接受未知格式。
- 修override有效源、整份模板current/legacy/drift状态解释、一般消费者doctor、handoff恢复和真实可观察契约。已核实旧完整模板才能迁移，未知本机修改保留/拒绝。
- 用户D11：默认先筛选决策链，真正值得用户决定的实质取舍才用grill；按优先级和依赖分轮，独立ready项才同批。明确研究/事实/局部实现/已定选择免问；执行实质歧义立即报告，在native规划阶段提问，不假定技术模式就是用户意图。
- 核心交付为完整grill整理和精炼用户准则；决策树逐步演进，不要求一次枚举全部问题。按指定上游grilling核验并适配原生工具/授权；答案新开/淘汰分支、证据阻断和充分收口有明确合同。design包含完整Skill草案及11项Skill必要改动矩阵，前序全部问题仍须收敛。
- 用户新增：证据工作可按价值使用subnode/grok等辅助，先保存决策断点，独立派发仍守原生批准门，事实回报不替用户作选择。完整用户模板不保留begin/end，adapter/catalog不再依赖块提取/合并，核验后整文件原子替换；未知改动保持。
- 组件 commit 推送 origin/main；保持系统 skill-installer 对集合安装的原生所有权；更新实际模板 digest/catalog，静态 AGENTS 单独升级。
- 当前只规划，无本 task 封口后批准，不实施、不发布、不操作安装副本。

## Acceptance Criteria

- [ ] 非法/缺失/null description、重复键和错误名称被拒，quoted name及全部真实Skills通过。
- [ ] 旧完整digest安全迁移，未知正文/drift/symlink拒绝并保持；完整模板current准确，旧组件专属marker消失。
- [ ] 精炼草案保留原有效语义；完整grill的筛选/单个frontier/优先级/依赖分轮/新开或淘汰分支/证据未完成与充分收口/即时升级有正反例，免问边界不膨胀；关联Skill触发与调用者一致。
- [ ] override与非默认CODEX_HOME有效源可诊断，不自动覆盖；全局没有特定Trellis状态/命令合同。
- [ ] doctor无源码checkout消费者、handoff研究/执行/完成阶段、组件路由正反例均通过有意义验证。
- [ ] 受影响测试通过、源码发布与安装版本一致、无本任务staging/临时残留，证据回根。

## Notes

- 根 issue-ledger/research 为证据入口，不复制用户配置、私有receipt或组件外源码。根审批不能自动充当本任务批准；必须将本任务当前 seal 明确纳入展示的审批包。
