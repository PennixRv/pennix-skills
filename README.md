# pennix-skills

用户自维护的 Codex 工作流 Skills 源码。

通用 Trellis Skill 随 Trellis 组件交付；本仓库只维护用户工作流策略、确定性辅助脚本和
对应测试。各 Skill 可独立安装到 Codex 的 Skill 发现路径，不使用额外的全局 manifest 或
运行时状态表。

安装使用 Codex 官方 `skill-installer` 提供的 GitHub 安装流程，例如：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo PennixRv/pennix-skills --path \
  skills/codegraph-project-setup skills/evidence-report skills/parallel-work skills/review-gate \
  skills/session-handoff skills/trellis-context-curation skills/trellis-research-record skills/workflow-doctor
```

可按需删减路径；`review-gate` 需要同时安装 `evidence-report`，因为它复用同一报告合同。源码变更应先提交并
推送本仓库，再重新安装对应 Skill。安装副本不是源码编辑位置，也不生成第二份版本或状态事实。
