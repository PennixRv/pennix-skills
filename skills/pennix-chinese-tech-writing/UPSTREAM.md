# 来源与适配

- 上游：[Fenng/Tech-Doc-Style-Chinese](https://github.com/Fenng/Tech-Doc-Style-Chinese)。
- 已审查提交：`b119d01c9bb7cd132b3c62fafdff34227c4410d1`。
- 原 Skill 名称：`tech-doc-style-chinese`。
- 许可：MIT，Copyright (c) 2026 Fenng；完整原文保留在 [LICENSE](LICENSE)。

`PennixRv/pennix-skills` 以 `pennix-chinese-tech-writing` 维护适配版；它不是自动同步快照，也没有独立 fork 仓库。

原有四份参考来自固定上游提交。术语参考调整引号与称呼约定，说明准确组件名称和通行英文术语，并以原生语义编辑接口替代上游段落改写命令。入口覆盖中文技术内容；新增的 `references/workflow-assets.md` 是本仓库自定义参考，明确新增文档语言、Trellis 原生机械惯例优先以及用户规则、Skill、思源笔记的写作边界。写作方法不授予持久化或生命周期权限；项目覆盖参考仍只是示例。

`scripts/lint_copy_rules.py` 与 `tests/test_lint_copy_rules.py` 保持上游行为。标准库脚本只读；警告和样式建议需要人工判断，上游引号建议不能覆盖本集合的常用中文引号约定。未引入写入型 `unwrap_md_paragraphs.py`、上游 CI 或按篇幅判定结构的测试。

后续更新先对照固定提交审查上游变化，保留许可、本地接口及格式优先边界，测试只读脚本并更新本记录；不自动覆盖适配入口或项目约定。
