---
name: trellis-document-governance
description: Use before creating or updating Trellis workflow, spec, task, research, report, journal, project Skill, agent, prompt, or final communication assets. It resolves the applicable AGENTS.md rules, applies the project document contract, and separates deterministic structure checks from main-session semantic review.
---

# Trellis 文档治理

在当前根项目创建、修改或审查 Trellis 文档资产时使用本 Skill。它负责把规则加载、文档
类型要求和验收动作固定下来；它不是权限控制、沙箱或任务事实来源。

## 适用范围

包括 `.trellis/workflow.md`、`.trellis/spec/**/*.md`、`.trellis/tasks/**`、
`.trellis/workspace/**`、`.trellis/agents/**`、`.agents/skills/trellis-*`，以及由这些
资产产生的研究、审查、交接和最终沟通。组件仓库的源码和组件仓库内部文档不在本 Skill
的修改范围内，除非当前任务明确以该仓库为目标。

## 调用顺序

处理项目文档资产时，先使用全局 `$trellis-project-document-governance` 解析通用项目规则、
文件所有权和文档类型合同，再使用本项目的 `trellis-document-governance` 补充本地
`.trellis/spec/operations/` 要求、任务路径和结构检查命令，最后由主会话完成语义审查。
本 Skill 是项目补充层，不替代全局入口，不复制其正文，也不保证宿主自动调度两个 Skill；
调用链只是明确责任和顺序的执行合同。

## 工作顺序

1. 先确定目标文件的实际所有权和目录范围；不要把组件源码、`/home/penn/.codex` 镜像、
   凭据、缓存、日志、数据库或会话状态复制到根仓库。
2. 从目标目录向仓库根目录检查适用的 `AGENTS.md`。运行时已注入的更高层系统、开发者
   和用户指令继续优先；更近的项目 `AGENTS.md` 优先于父目录规则。不要复制外部
   `AGENTS.md` 全文，项目 spec 只记录可执行的引用关系和补充契约。
3. 读取 `.trellis/spec/operations/document-governance.md`，再读取当前任务的 `prd.md`、
   `design.md`、`implement.md` 或报告要求。任务文档不能放宽 `AGENTS.md` 或 spec 约束。
4. 按文档类型写作：
   - PRD：目标、需求、约束、验收标准；不混入技术实现清单。
   - 设计：边界、数据流、契约、取舍、兼容性、回滚。
   - 实施计划：有序步骤、验证命令、门禁和回滚点。
   - 研究/审查/交接：问题、证据位置、已确认事实、推断、未确认项、影响和建议。
   - spec：适用范围、触发条件、签名/输入输出、契约、错误矩阵、案例和测试。
   - journal/最终沟通：先给结论，再给完成项、证据、缺口、风险和下一步。
5. 默认使用正式、紧凑的简体中文。命令、路径、配置键、协议字段、版本号、日志和错误
   原文保持不变；必须保留的用户原文按要求保留。确需英文术语时，同时说明其具体
   职责、动作或影响，不用未解释的抽象黑话。
6. 写完后运行确定性的结构检查：

   ```bash
   python3 .agents/skills/trellis-document-governance/scripts/check_structure.py \
     --root . --paths <changed-file-or-directory>...
   git diff --check
   ```

   结构检查只验证文件范围、文本编码、标题形式、链接目标、JSON 语法和文件数量；它不
   读取或输出文档正文，也不宣称语义质量通过。
7. 主会话继续完成语义审查：确认结论前置、证据可核验、事实与推断分开、风险和未确认项
   明确、职责边界一致、索引和状态真实。工作节点报告只能作为候选证据，不能直接晋升
   为任务事实。
8. 归档时，先让工作资产完成独立提交；随后执行

   ```bash
   python3 .trellis/scripts/task.py archive <task-dir> --no-commit
   python3 .agents/skills/trellis-document-governance/scripts/check_structure.py \
     --root . --paths <actual-archive-directory>
   python3 .agents/skills/trellis-document-governance/scripts/check_structure.py \
     --root . --tracked-markdown --links-only --max-files 1000
   git diff --check
   ```

   `<actual-archive-directory>` 必须取自刚才归档命令的实际输出，不得按日期或目录层级猜测。
   第一项检查刚归档任务的出链，第二项检查当前工作树中 Git 跟踪或待提交的 Markdown 文档对旧
   活动路径的入链，避免把未跟踪的数据库、备份和运行时文件混入文档门禁。任何结构检查失败时，
   主会话只修复报告中已确认的断链，重复同一组检查；不得批量改写历史链接、改变任务事实或宣称
   Trellis 上游已修复。随后再单独完成语义审查，记录实际目录、命令、结果和未确认项。
   更新模板或恢复会话后，重新检查链接、索引、活动任务路径和本 Skill 是否仍可达。项目级
   Skill 位于 bundled Skill 之外，不修改公共 bundled Skill 的正文。
9. 当前项目的 `check_structure.py` 是已物化副本。修改全局
   `/home/penn/.codex/skills/trellis-project-document-governance/` 的同一检查器行为时，必须明确
   同步本副本，并运行：

   ```bash
   cmp -s /home/penn/.codex/skills/trellis-project-document-governance/scripts/check_structure.py \
     .agents/skills/trellis-document-governance/scripts/check_structure.py
   ```

   只有比较通过、全局测试通过且本项目以副本完成实际检查后，才能声称当前项目已继承该行为。
   这不是其他项目自动更新的声明；其他已物化副本必须由各自项目单独核验。

## 检查结果的表达

把自动检查和语义审查分别报告：自动检查给出命令及 `pass/fail`；语义审查给出文件位置、
规则、证据和修复方向。发现缺口时直接说明，不用“已优化”或“已验证”替代具体证据。

## 相关规范

- `.trellis/spec/operations/document-governance.md`：长期契约和错误矩阵。
- `.trellis/workflow.md`：阶段、路由和提交门槛。
- `.trellis/spec/operations/workflow-governance-current.md`：当前任务事实、工作节点和 Git 所有权。
