# 实施步骤

1. 根任务获批准并启动本子任务后，核对源仓库基线和模板来源，不手改 `~/.codex/AGENTS.md`。
2. 修改权威用户模板与既有 routing 合同测试；待 Trellis 发布回执确定后更新 catalog approved version，并重算模板 revision。
3. 运行 `python3 -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'`、`python3 -m unittest discover -s skills/pennix-component-lifecycle/tests -p 'test_*.py'`、`python3 -m unittest discover -s skills/pennix-chinese-tech-writing/tests -p 'test_*.py'`，并对明确修改的 Markdown 运行现有文案 linter。
4. 按 Pennix Skills 原生任务提交并推送；使用 `$skill-installer` 和 lifecycle 暂存替换/升级路径安装，随后运行 `discover`、`verify`，核对模板摘要和收据。
5. 将 commit、template revision、catalog pin、安装回执和宿主行为验证限制写回本子任务及根任务。
