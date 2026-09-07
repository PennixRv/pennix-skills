# 验收记录

## 已完成的源码验收

- 已删除 `parallel-work`、`evidence-report` 和 `review-gate` 的全部受控 Skill 文件；没有保留
  wrapper、terminal JSON transport、sandbox 指令或独立的用户级报告 schema。
- `pennix-workflow-routing` 和 `trellis-research-record` 仅将显式独立取证路由到项目选择的
  Trellis `subnode` procedure，不复制其 contract 或 lifecycle。
- `python3 -m unittest discover -s skills/pennix-skills-install/tests -p 'test_*.py'`：8 tests passed。
- `python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py'`：8 tests passed。
- `quick_validate.py` 已验证全部 9 个保留 Skill。
- `install.py --source <checkout> --check` 通过；临时 host destination 安装 9 个 Skill，确认不存在
  `parallel-work`、`evidence-report` 或 `review-gate`。

## 发布后验收

- 提交 `0f334cd` 已推送至 `PennixRv/pennix-skills` 的 `main`。
- 已通过显式安装器将该 revision 原子重装到
  `/home/penn/.codex/skills/pennix-skills`；安装副本只包含 9 个保留 Skill，确认不含
  `parallel-work`、`evidence-report` 或 `review-gate`。
