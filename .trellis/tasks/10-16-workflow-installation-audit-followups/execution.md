# 实施记录

## 授权与修改边界

用户阅读根侧完整四项方案后明确答复“批准”。根侧和本任务均已原生 seal revision 1、approve、start，当前为 in_progress；进度只写本记录，不修改已封口材料。

修改目标为本仓库 main：catalog 纳入 pnpm 并对齐两个已核验版本；`scripts/adapters/skills_install.py` 负责精确暂存快照与丢弃；`scripts/lifecycle.py` 负责公开参数和结果；新增实际文件系统行为测试并沿用 npm 迁移回归；lifecycle Skill、resource-cleanup Skill 与资源策略说明新入口。安装副本只由系统 installer 与原生 replace 更新。

差异验收覆盖调用入口、默认只读、完整摘要、路径／owner／链接拒绝、目录替换和删除失败，以及原有集合／收据／命令不变。保留 Trellis 的 pnpm pin 和 beta 分支、Paseo daemon、既有配置选择及其他资源。

## 结果

- lifecycle 完整回归：`python3 -m unittest discover -s skills/pennix-component-lifecycle/tests`，200 项通过；其中暂存丢弃新增 12 项。最初 CLI 夹具错误影响了 catalog 的同名校验函数，已改用真实清单成员，完整回归随后通过。
- 两个受影响 Skill 的 system quick_validate 均通过；中文检查 error=0、warning=0，6 条引号样式建议涉及既有正文，按本集合保留中文弯引号的约定不改写。
- 主会话按 trellis-check 复核 CLI → adapter → 原生删除及 catalog → 既有 npm 迁移的调用链，确认默认预览不调用全局 discover、不创建收据；活动集合完整性摘要合同不变。核验与删除的非事务限制已保留在源码及说明。
- `git diff --check` 通过；没有新增依赖或未解决的实施范围问题。准备提交推送源码，再安装该精确提交并进行实机验收。
