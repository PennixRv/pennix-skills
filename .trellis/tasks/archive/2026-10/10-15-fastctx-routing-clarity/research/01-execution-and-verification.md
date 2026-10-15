# 实施与验收记录

## 授权与基线

用户明确批准两项任务 revision 2 的完整修订包进入实施，并授权修复、提交推送、必要发布、重装、落点更新与任务收敛。根侧和源侧均已原生记录该版本的批准并启动；本次授权也覆盖封口计划中的后续发布和物化，无需重复索取同范围确认。

源仓库基线为 `da0ee0c6e68575c4143f885100349d5c55fda066`，实施分支为 `task/fastctx-routing-clarity`。已安装模板为当前完整版本且实际生效，`pennix-skills` 集合完整性为 `match`、PyYAML 就绪。模板旧发布来源为 `1417191`，精确摘要沿用设计快照并由固定夹具核验。

修改范围为已封口的三份正文、模板 revision、精确旧版识别、既有升级测试和夹具。本任务不调整 FastCtx runtime、Trellis runtime、Codex fork 或 Hook。

## 固定行为输入

E1–E4 使用既有四个场景原文。前后使用同一份用例 digest；另两项固定输入如下，均不预先加载专项 Skill，不提供预期工具路径。

- E5：读取无秘密 fixture 的 `AGENTS.md` 与 `.trellis/spec/index.md`，报告两份文件的标记。fixture 标记分别为 `routing-bootstrap-marker`、`routing-spec-marker`。
- E6 第一轮：仅在批准根项目查询原生 `task.py --help` 并简述用途。
- E6 第二轮：延续第一轮真实会话，只读查询根项目 `task.py current --json`，完整读取根任务 PRD 与 `root-coordination.md`，报告状态和文件主旨；不绑定或启动任务。

只允许上述无秘密 fixture、已发现 Skill 及必要 references、根项目 `AGENTS.md`、workflow、规范和指定任务文档；不访问其他项目、历史会话或秘密，不安装配置，不写入项目或模拟原生协议。E6 通过第一轮实际 thread ID 原生 resume，不使用 `--last` 或拼接历史。

所有原始轨迹、stderr 和预算只存私有临时目录。本任务最多十四个模型轮次，不自动重试；被阻塞或未触发的场景如实记录，不采样到成功为止。

## 当前执行

旧安装版本的 E1–E6 已完成，共七个模型轮次；E6 第二轮通过第一轮实际 thread ID 原生 resume。安装在全部前测完成前保留旧版。E1–E5 与 E6 第一轮均出现首次 Skill 读取走宿主 shell；后续转用 FastCtx、读完文件或正确调用 Trellis 不能抵消该动作的失败。E6 第二轮将 PRD/规范读取交给 FastCtx、`current --json` 交给原生宿主，逐动作路由正确；该新评估会话没有任务绑定，原生命令返回 `current_task: null`、`source: none`、非空 `session_source`，未伪造绑定。既有采集器的 `review_needed` 与粗分类不是通过凭据。

源码首次检查：lifecycle 全部 179 项测试通过；两份 Skill 结构校验通过，三份正文中文检查无 error/warning。集合其他模块检查发现两份 routing 的旧测试要求原句和重复段落；这属于已改正文的必要调用方适配。现将相关检查收敛为参数标识与跨 Skill 依赖/委托链接可解析，删除过时措辞断言；它们只证明静态合同可达，不作为行为验收证据。其余已通过模块保留结果，只重跑修改过的测试。

复发分析：历史上已出现普通读取与 shell 混用；本次也没有 FastCtx 服务不可用的实际回执。已证实的问题是规则未落实到首次读取和逐动作边界，以及粗分类不足以发现这一点。压缩造成规则丢失仍无直接证据。本次将短默认放入常驻用户规则、完整合同集中于 FastCtx Skill，并在质量规范中记录真实轨迹检查要求；不据此预先宣称行为问题已解决。

静态门禁收敛：按现有 CI 入口执行全部 Skill 测试及评估器测试；已通过模块结果复用，修改后的 FastCtx 三项和 workflow 七项单独重跑通过。当前总计 281 项，含一项既有跳过；生命周期 179 项包含完整旧模板升级、个人漂移拒绝及写入失败保护。两份 Skill 校验有效，正文中文检查无 error/warning，`git diff --check` 通过。历史模板夹具与发布摘要精确匹配。

## 发布与物化

- 产品提交 `6ec081169f873853ee05153a9fe49f2c00193abd` 已快进合入并推送 `main`，随后用 `git ls-remote` 核对远端精确提交。集合由 Git 来源发布，不新增运行时包版本或标签。
- 系统 `$skill-installer` 使用该完整提交、catalog 的全部源路径与 `--method git` 下载到新的相邻暂存。原生集合校验确认精确入口、有效 frontmatter 与可执行 seed，再从新暂存运行 `replace-staged --component pennix-skills --yes`，返回 `changed`。
- 新活动入口执行 `upgrade --component codex-agents --yes` 返回 `changed`；两项分别定向 `verify` 均为 `match`、failures 为空。后续 discover 显示集合完整性 `match`、用户规则 `current` 且 `active`、profile `match`；未执行不必要的状态协调，也未修改无关组件漂移。
- 两份路由 Skill 和 catalog 安装字节与源提交一致。用户规则 SHA-256 为 `bc6b0ab4d5f5ee4d01952341a6b8fdd6685e949981ac6b5acd92540e9c5bae68`，精确匹配新模板。系统安装器的新 Skill 可在下一轮发现。
- 根仓库 `node scripts/run-workflow-integration.mjs --offline` 退出 0，八项全部通过，包含源集合与项目只读边界；执行期间未并行修改根项目状态。
- 同组后测在物化核对完成后启动，保持原 fixture digest 与输入；最终结果见下文。

## 实施中的验收调整

用户在看到后测首读偏差后明确表示：“首读偏差我认为是能接受的必要小瑕疵”。这是对同一修订包验收的有界调整，不新增组件、实现或模型轮次，任务保持 `in_progress`。冻结的 revision 2 文档作为原计划保留；本节记录后续有效取舍。

首次加载规则或 Skill 的入口偏差作为用户接受的残余瑕疵，原轨迹中的失败事实与前后差异仍保留，不改写为首读已修复。加载后的普通文档读取、搜索、实际 Partial 续页及组件原生边界仍须按合同验收；不将该取舍扩大为任意 shell 读取或模拟 Trellis 协议的许可。剩余同组测试按原十四轮上限完成，不采样重试。

## 固定后测结果

实际宿主为本机原生 Codex exec，只读沙箱，禁用原生代理；CLI `0.162.1`、FastCtx `0.2.29`、Trellis `0.7.0-beta.50`。未覆盖或猜测实际模型名称，采集事件中的模型信息为空。E1–E4 的前后 fixture SHA-256 一致，均为 `f746a75d6729033a6b0b9d9907a712e5c66c12b93587e6a7f0a81683f4072fe1`；E5–E6 沿用上述固定 prompt。

| 场景 | 后测逐动作结果 | 首读残余 |
| --- | --- | --- |
| E1 普通读取与搜索 | fixture 全文读取及 marker 检索均走 FastCtx | 首次 Skill 读取走 shell，目标路径错误后经 FastCtx 定位；已接受 |
| E2 Trellis 反例 | 普通文件走 FastCtx，`trellis --help` 与 `trellis task --help` 走宿主原生入口，均退出 0 | 初始两份 Skill 读取走 shell；已接受 |
| E3 有界长文本 | 真实 Partial 为 1–8、9–16、17–24 行，严格沿返回 offset 续读 | 初始 Skill 读取走 shell；已接受 |
| E4 混合检索与续页 | 两份文件独立 FastCtx 检索；长文本 1–3 行后沿 offset=4 读取 4–6 行；Trellis help 独立原生调用 | 初始 Skill 目标不存在，保留路径错误并用 FastCtx 定位；已接受 |
| E5 盲测 | 两份指定文件由 FastCtx 批量完整读取，两项标记正确，返回 Complete | 初始 Skill 读取走 shell；已接受 |
| E6 连续两轮 | 第一轮项目规则通过 FastCtx 读取并补全真实 Partial，再原生调用 task.py help；第二轮原生 current 查询与 FastCtx PRD/规范批量完整读取分开，未修改绑定 | 第一轮初始两份 Skill 读取走 shell；已接受，第二轮无普通读取偏离 |

E2/E4 的 fixture 没有项目 task.py，实际调用已安装的 Trellis 原生 task CLI help 成功；没有模拟任务协议。目录错误、容量保护、副作用重放和真实压缩恢复未主动注入或触发，不把未覆盖分支标为行为通过。首次目标路径不存在只证明该路径错误，不能凭模型自述归因为宿主 Skill 清单错误。

前后各七轮全部原生完成，共十四轮，无重试；原始轨迹仅存本机私有 `/tmp/fastctx-routing-recurrence.DhSMtg/`。E6 后测第二轮的 `current --json` 退出 1，回执为 `current_task: null`、`source: none`、非空 `session_source`、`stale: false`，与独立评估会话未绑定任务的预期一致；这不是协议能力缺失，未复制主会话身份或绑定。两轮通过第一轮实际 thread ID 原生 resume，未拼接历史。

## 验收结论与收敛

- AC1、AC2：逐份复核正文差异；常驻默认、完整操作合同和跨组件分流职责收敛，错误类别、原生嵌套、Partial、原生协议与副作用保护仍保留。
- AC3：新 revision 与模板摘要一致；179 项生命周期测试和真实旧版升级验证通过，个人漂移与原子写入保护未放宽。
- AC4：原严格首读条件的失败事实保留，并按用户实施中明确接受的残余处理。六个后测场景加载后的普通读取、搜索、实际续页、Trellis 边界与跨轮动作切换均符合约定；不能据此宣称首读已修复或量化证明长期稳定性提高。
- AC5：用户完整部署授权已经满足，Git 发布、系统安装、定向 verify、源与安装字节一致性及根侧八项集成门禁都有实际证据。

本修订包按调整后的验收条件可收敛归档；首读偏差是已接受限制，不留作未经说明的已修复项。未扩展运行时、Hook 或其他组件，未修改凭据与无关配置漂移。剩余未触发条件保留为验证边界，不追加本轮模型预算。
