---
name: pennix-trellis-asset-check
description: 只读诊断已初始化 Trellis 项目的生成资产、Skills 和迁移残留；可选地检查本地 fork 检出目录。
---
# 工作流诊断
在项目根目录运行只读诊断：
```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/pennix-trellis-asset-check/scripts/doctor.py" --project-root .
```

输出会区分项目必须具备的生成资产，以及可选的本地 Trellis 源代码检出和包信息。普通消费者不需要 `Trellis/` 检出目录。`degraded` 是诊断信息，不是悄悄修复或安装任何内容的授权。检查报告文件的归属仓库，再明确选择下一项任务。

`pass` 只表示固定路径存在，且 `.agents/skills/` 的非隐藏直接子目录具有 `SKILL.md`。脚本还报告可选 `Trellis/` 检出状态、包名和旧 `.trellis/codex-workflow.json` 路径；这些报告项不构成全面验收。它不验证 frontmatter、正文语义、版本或摘要匹配、任务阶段、工作流运行正确性、其他组件接入与整体健康。若请求需要这些结论，转到具体 owner 的核验入口，不能把本报告扩写成“工作流已通过”。

本 Skill 不探测服务商、不修改 Codex 配置、不停止工作节点、不安装包、不删除插件缓存，也不写入任务事实。不得用它替代 Trellis 自己的 Channel 生命周期命令。
