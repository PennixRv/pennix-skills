# 补齐额外发现决策与安装版本落点

## Goal

负责根协调任务 `workflow-principle-enhancement` 中 Pennix Skills 的权威源码、固定版本清单及用户级安装落点：让 decision grill 明确处理额外发现的范围选择，增强中文技术写作 Skill 的落笔前载体/骨架辨析方法，修复经用户选择纳入的 `tmux` 版本漂移，并在 Trellis beta 发布后更新和部署 Trellis CLI pin。

## Requirements

- `pennix-decision-grill` 对规划或实施中新发现的、与任务相关且经核验的问题，要求说明关联性、维护目标、影响/成本及选项，推荐后询问是否纳入当前任务、另立任务或不纳入。
- 按主线 D15，decision grill 在封口前回看原始需求，确认主线的重要选择没有遗漏，不因额外问题均已答完就判定整体收敛；主线未决项优先处理，旁线记录并确定落点后回主线。复用当前任务记录，不建立完整方法链或新增台账。
- `pennix-chinese-tech-writing` 在撰写 Trellis 资产前，要求先读取项目指引和目标资产的实际模板/生成源，区分固定骨架、机器结构与自定义正文；保留原生结构，以简体中文起草自定义正文，除非有明确、可核验的语言例外。不得从英文示例本身推断正文语言。
- 已有明确纳入授权时继续规划，不重复询问；纳入规划不等于实施授权。发现会改变封口范围时仍走现有 Trellis replan/seal/approve 生命周期。
- 修订现有 Skill contract test，覆盖新决策、既有授权、范围变化与实施批准边界，不增加新的决策状态机。
- `component-versions.json` 将 tmux 固定版本从经证实过时的 `3.7c` 更新到仓库和已安装状态都匹配的 `3.8`，保留 pinned 版本和 mismatch 拒绝策略。
- Trellis CLI pin 只在配对 npm beta 真实发布并验证后更新到该版本；当前 `.44` 是候选，执行时需复核实际发布版本。
- 移除 Pennix 项目自有 guide copy 中无依据的固定 35% 假阳性率，保留逐项基于实际代码核验的规则。
- 仅用 `$skill-installer` 和 `$pennix-workflow-lifecycle` 的原生路径部署、验证；不改安装副本/缓存、不接触密钥或 tmux 运行态。

## Acceptance Criteria

- [ ] Decision grill Skill 与 contract tests 同时表达原始需求/主线未决项的封口核对，以及“先核验额外发现、让用户选择范围、遵守已授权范围且不混淆实施批准”。
- [ ] 中文技术写作 Skill 的入口与载体参考共同表达落笔前载体核验、固定结构保留、自定义正文语言选择和有证据的例外；不增加语言扫描器或改变 Trellis 生成骨架。
- [ ] catalog/lifecycle tests 通过；tmux 3.8 pin 与实际 3.8-1 安装验证一致，Trellis CLI catalog pin 与已发布 CLI/Core 双包版本一致。
- [ ] 用户级 Skills 集合从已推送源经原生安装器 staging、receipt 和 `replace-staged` 更新；lifecycle `discover`/`verify` 成功，无手改活动安装副本。
- [ ] Pennix 项目自有 spec copy 只移除无来源百分比；适用项目更新 dry-run 与根集成验收通过。
- [ ] 本任务在原生 Planning Seal 后保持等待明确后续批准，批准前不修改产品源码或系统状态。

## Constraints

- Source branch: `main`; `pennix-skills` 是独立 Skills 源仓库，不是 Trellis runtime 源。
- Trellis npm 发布先于其版本 pin 更新；tmux 已安装且候选均为 3.8-1，预期只需更新 catalog、重装 Skills 和原生 verify。
- 不访问 Office WSL 或真实 Codex 历史，不重设可选服务、凭据或系统包。
