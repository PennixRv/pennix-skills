# 实施计划：可重入 Seed 与完整原生 Collection

1. 将 seed 的配置/凭据前置检查改为按文件缺失情况创建，扩展测试覆盖 fresh、
   完整重入和单文件修复，不改变 secret 输出与权限合同。
2. 用第一个会话的 lifecycle bootstrap 与第二个会话的 lifecycle prompt 替换
   bridge/source-checkout 完成文案，并同步 README 与 lifecycle Skill。
3. 从 catalog 导出 bootstrap 与剩余 collection 的安装合同；将 `pennix-skills` 的
   discover/verify/uninstall 改为完整安装副本或精确 bootstrap 合同，取消目标机
   checkout-backed install/upgrade 声明。
4. 更新 collection/lifecycle 单元测试和文档断言，检查子 Skill 清单不会泄露到
   seed 用户提示。
5. 运行 shell syntax、Seed、lifecycle、collection 和全量 Python CI；审查 diff、
   评估 spec 更新、提交并推送。

## Rollback

代码回滚只需恢复本任务提交。宿主现有 `config.toml`、`auth.json` 和 Skills
collection 不由本任务测试或代码修改；没有运行目标机的写入式 seed 操作。
