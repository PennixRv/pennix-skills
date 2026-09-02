---
name: trellis-context-curation
description: "仅在用户明确要求整理已初始化 Trellis 项目的规格、调研资料或任务上下文清单时使用。审查或重组 .trellis/spec、任务 research、implement.jsonl、check.jsonl；不用于普通任务恢复、头脑风暴、规格更新或质量检查。"
---

# Trellis 上下文整理

在不损失当前任务所需事实的前提下，缩小 Trellis 额外加载的资料范围。仅处理已初始化的项目；只在用户明确要求或当前 Trellis 流程明确路由到本 Skill 时使用。不执行 `trellis init`，不替代 `trellis-continue`、`trellis-brainstorm`、`trellis-update-spec` 或 `trellis-check`，不改写任务状态、`RecoveryBrief` 或 context-mode 的职责。

## 工作流程

1. 确认项目根目录存在 `.trellis/`，识别当前任务与实际加载路径；未初始化或没有明确目标时，先报告范围，不创建项目资产。
2. 使用项目提供的 `task.py list-context <task>` 等接口确认当前清单，再审计 `.trellis/spec/`、当前任务的 `research/`、`implement.jsonl` 与 `check.jsonl`：列出重复内容、过宽引用、失效链接和缺失的必要资料。
3. 先提出最小重组方案；涉及任务范围、契约语义或删除现有资料时，取得用户或当前项目规则要求的确认后再改动。
4. 按 [资料整理契约](references/curation-contract.md) 重组。新增或调整任务上下文引用时，优先使用项目的 `task.py add-context` 等接口，不直接手写 JSONL。保留现有项目结构和项目 `AGENTS.md` 的更具体规则；不要为了统一目录而做无关迁移。
5. 验证索引可达性、链接和清单引用、当前任务的资料充分性，以及 Trellis hook 和 worker 的读取兼容性；验证强度仍与风险相称。

## 不可破坏的边界

- `implement.jsonl` 与 `check.jsonl` 仅列出当前任务额外需要的规格叶文件和调研摘要；不引用 `AGENTS.md`、规格或调研索引、`research/evidence/` 或无关资料。
- 这两份清单不替代 Trellis 工作节点的必读任务事实。工作节点仍须按 Trellis 协议读取当前任务的 `prd.md`，并在存在时读取 `design.md` 与 `implement.md`。
- 完整调研证据只在质疑摘要结论、解决冲突或调查未决问题时加载。不得借由整理跳过必要测试、配置检查或风险验证。

需要具体拆分、索引和清单规则时，读取 [资料整理契约](references/curation-contract.md)。
