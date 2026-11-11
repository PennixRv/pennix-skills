# 四类文档阅读技能

本记录执行根任务已批准 design.md 的 WP1。根任务位于 ../.trellis/tasks/in_progress/11-10-office-pdf-reading-skills；完整方案 revision 为 8500d1f82fa67698195ba3a97f47a7121bb8005e62a4c50a81fb492237a7d9e9，真实用户答复为“认可”。

skills/docx、pdf、pptx、xlsx 来自 anthropics/skills@2c5958ecac7cee2b583967a2c4981d0f4a75c579 对应子目录。本地衍生维护保留许可，附 UPSTREAM.md，原生补丁可与上游归档逐文件比较；不改既有 materialized 合同。collection.json 登记四项。仅适配中文发现、默认只读边界、运行时入口、PDF 引用、唯一临时渲染目录及移除 soffice 权限规避代码；保留上游其他方法。

Python 由 Lifecycle 管理的 markitdown uv tool 环境提供，使用 uv 原生目录及 receipt 核对后选择其 Python，不引入第二安装器。系统依赖同归 Lifecycle。现有 workflow-routing 参考只补四类方法与组合边界。

## 决策

<!-- trellis-decisions:v1 -->
```json
{"decisions":[{"id":"approved-wp1","status":"resolved","question":"来源、集合和阅读范围如何确定？","evidence":["根任务 design.md、implementation-approval.md"],"answer_or_reason":"复用同一已批准 WP1：固定 Anthropic 四项进入主集合，完整本地阅读，保留生成方法但不扩展生成验收。","impact":"主集合内容与文档；依赖及正式安装由 Lifecycle 和根任务完成。","reopen_when":"需要新仓库、manifest 扩展或改变验收范围时。"}]}
```
