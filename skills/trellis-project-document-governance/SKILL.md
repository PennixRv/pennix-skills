---
name: trellis-project-document-governance
description: 在任何项目创建、更新、审查或归档 Trellis workflow、spec、任务、研究、报告、journal、项目 Skill、agent 或 prompt 时使用。它加载适用的 AGENTS.md，区分确定性结构检查与主会话语义审查，并保留项目更具体的文档规则。
---

# Trellis 项目文档治理

1. 确定目标文件的项目根、实际所有权和适用范围。不要把组件源码、用户级 Codex 静态环境、凭据、
   cache、会话或运行时状态复制到文档资产。
2. 从目标目录向项目根解析所有适用的 `AGENTS.md`；运行时已注入的系统、开发者和用户指令继续
   优先。项目存在更具体的文档治理 Skill 时，优先遵循该项目 Skill 的补充契约。
3. 读取当前项目的 `.trellis/workflow.md`、相关 operations/spec 与活动任务材料，再按资产类型
   写作：PRD 写目标、需求、约束和验收；设计写边界、数据流、取舍和回滚；实施计划写步骤、门禁和
   验证；研究、审查和交接写问题、证据、已确认事实、推断、未确认项、影响和建议。
4. 默认使用正式、紧凑的简体中文。结论先于展开说明；命令、路径、配置键、版本号和错误原文保持
   原样。事实、推断和未确认项必须分开表达。
5. 先运行确定性结构检查，再由主会话完成语义审查：

   ```bash
   python3 "$CODEX_HOME/skills/trellis-project-document-governance/scripts/check_structure.py" \
     --root <project-root> --paths <changed-file-or-directory>...
   git -C <project-root> diff --check
   ```

   结构检查只覆盖显式路径、UTF-8、空文件、Markdown 标题、项目内链接、JSON 和文件数量；它不
   判断事实、证据或语言质量。主会话必须独立核对结论顺序、证据、职责边界、索引和任务状态。
6. 归档后若项目规则要求检查旧活动路径的入链，使用当前工作树的受控链接模式，而非将整个
   工作树交给 `--paths`：

   ```bash
   python3 "$CODEX_HOME/skills/trellis-project-document-governance/scripts/check_structure.py" \
     --root <project-root> --tracked-markdown --links-only --max-files <approved-limit>
   ```

   `--tracked-markdown` 只发现版本化和未忽略的待提交 Markdown 文件，并过滤当前已不存在的索引
   旧路径；`--links-only` 只核验 UTF-8 与项目内链接，不替代针对明确文档资产的完整结构检查。
   项目仍须定义其 archive 目录检查、文件上限和失败处理。
7. 工作节点报告始终只是候选证据。只有主会话核验后，才能写入 Trellis 任务、spec、issue 或
   最终交接。归档或模板刷新后重新检查活动任务路径、相对链接和项目级 Skill 的可达性。
