# 执行计划

1. 复核两份 Skill、集合清单和现有生成/检查入口；核对 `windsurf-code-search` 已完成来源提交及实际 SHA。
2. 最小修改 `pennix-context-mode-integration` 的描述和正文，明确默认 Context Mode、执行/处理/索引的区别、有限负面清单、故障发现和原生回退条件。
3. 修改 `pennix-workflow-routing` 的冲突表达，使其引用集成 Skill 的唯一详细规则；保留各 owner 接口与现有本地检索顺序。
4. 通过集合原生生成器更新 Windsurf 固定来源并物化成员；运行集合完整性、引用、元数据、适用 lint/test 检查。
5. 审阅差异，提交并推送 `main`；记录源 SHA、Windsurf pin、生成结果和检查回执。
6. 在根任务后续 Lifecycle 安装与新会话验收完成后，核对集合物化字节，再按本仓库 Trellis 原生流程归档本任务。

不编辑安装副本、Context Mode Hook/执行器、其他 Skill、生命周期配置或用户运行态；不以集合文本检查代替根任务的新会话行为验证。
