# Pennix Skills 源码与安装设计

## 边界与所有权

本任务只维护 `pennix-skills` 源仓库：`pennix-decision-grill`、`pennix-chinese-tech-writing`、lifecycle catalog/测试和本项目自有 guide copy。Trellis CLI/Core 与其发布归 Trellis 组件任务；根任务拥有整体规划、根自有 guide copy 和最终集成。安装副本由 Codex `$skill-installer` 的 staging 加现有 `replace-staged` 所有，不在安装路径编辑。

## Skill 规则

按主线 D15，在 `pennix-decision-grill/SKILL.md` 的规划收口处增加原始需求核对：确认主线事项已定、由事实关闭或仍需用户选择，主线重要选择未关闭时不因额外问题已答完而收口；旁线确定落点后回主线。原有记录足够，不建立完整方法链、新字段或台账。

按 D01 增加“执行或研究中新发现”入口，接入已有 dependency-ready 决策链：先核验候选是否属实、与当前目标的关联、真实修改 owner、影响/成本；然后给出纳入当前任务、另立任务或不纳入的真实选项与推荐。用户已明确授权同范围纳入时不再问。发现纳入规划不代表可以改产品；材料性范围变化仍依原生 phase 返回 planning、封口并取得后续批准。避免把例行小发现变成强制提问，也不另造发现登记状态机。

在现有 `tests/test_contract.py` 增加短断言，要求主线原始需求核对、额外发现触发/核验/选项、授权复用和批准边界均有明确文本；测试只验证 Skill 合同，不声称模型必定遵从。

## 中文技术写作规则

在 `pennix-chinese-tech-writing/SKILL.md` 和 `references/workflow-assets.md` 中把已有的语言/格式原则落实为可执行的起草顺序：写作前先读取目标项目 `AGENTS.md`、适用 spec 和实际模板/生成源；标出文件名、章节骨架、frontmatter、schema、状态、解析标记、托管块及其他机器结构；先按这些合同搭好或保留固定部分，再与自定义正文分层撰写。自定义正文默认使用简体中文；只有项目或载体存在明确、可核验的其他语言要求时才使用例外。英文示例只说明其展示的结构，不自动决定自定义正文语言。

这项规则针对起草过程，终稿语义复核仍保留；不增加自动语言检测器、按字数判定的脚本或 Trellis task 生成器变更。用当前失误的 Trellis PRD/design/implement 作为人工验收样例，确认 `prd.md` 固定的 `Goal`、`Requirements`、`Acceptance Criteria` 标题仍为原生形式，自定义正文按中文默认值撰写，命令、路径、API 和字段保持原文。

## catalog 与项目 copy

- `component-versions.json:components.tmux.approved_version` 更新到 `3.8`，保持 `pinned` 默认行为和当前 mismatch gate。
- `components.trellis-cli.approved_version` 在 Trellis 配对 beta 通过 CI 发布并核验后，更新到实际发布版本；候选是 `0.7.0-beta.44`，不允许先于 npm artifact 更新。
- Pennix 自有 `.trellis/spec/guides/index.md` 仅删固定 `~35%`，保留 CRITICAL/WARNING finding 需按实际代码核验；不通过 CLI update force 写受保护 spec。

## 部署合同

源变更在 `main` 推送后，使用 `$skill-installer` 把完整集合安装到 `$CODEX_HOME/skills` 下的新临时 staging；检查声明的 Skill 名称/frontmatter/执行位后，从已核验 staging 调用其 `replace-staged` 到活动集合。替换成功后通过 lifecycle `discover` 与指定组件/全量 `verify` 验证。Trellis CLI 用 lifecycle 原生 `upgrade --component trellis-cli --yes`；tmux 3.8-1 已与新 pin 对齐时只 verify，不重复安装。Pennix 项目的 `.agents` 等生成资产通过 `$pennix-trellis-project-update` 的原生项目更新流程处理，保留本地受保护修改。

如果新 catalog 引用的 Trellis 版本尚未公开、Skill collection receipt 不匹配、tmux repository candidate 改变或 protected project candidate 含无关差异，停止对应部署并记录事实；不接受未知版本或强行覆盖。
