---
name: workflow-doctor
description: 只读诊断已初始化 Trellis 项目的生成资产、Skills 和迁移残留；可选地检查本地 fork 检出目录。
---
# 工作流诊断
在项目根目录运行只读诊断：
```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/workflow-doctor/scripts/doctor.py" --project-root .
```

输出会区分项目必须具备的生成资产，以及可选的本地 Trellis 源代码检出和包信息。普通消费者不需要 `Trellis/` 检出目录。`degraded` 是诊断信息，不是悄悄修复或安装任何内容的授权。检查报告文件的归属仓库，再明确选择下一项任务。

本 Skill 不探测服务商、不修改 Codex 配置、不停止工作节点、不安装包、不删除插件缓存，也不写入任务事实。不得用它替代 Trellis 自己的 Channel 生命周期命令。
