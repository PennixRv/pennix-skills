# CCH 固定版本同步设计

## 唯一修改点

`skills/pennix-component-lifecycle/references/component-versions.json` 的 `components.cch-status.approved_version` 从 0.1.45 改为 0.1.46。现有 native-owner 路径、集合合同、其他版本、配置目标和 AGENTS 模板均保留，不为单字段变更新增代码或镜像测试。

## 依赖与分支

依赖 CCH 仓库 main 的 0.1.46 修复及 GitHub Release、精确归档安装、doctor 与运行副本验收；CCH 失败时不提前声明新固定版本可用。当前源码 HEAD 和 origin/main 同为 1c1c1a4444bfb2f81ca5343dde3b00c21412bafe，工作树除本任务资产外无变化。本地 main 落后，批准后仅快进到核验基线再交付，不能 reset 或丢弃分支历史。远端变化时重核差异；影响本计划则重新封口。

## 部署合同

先以现行安装入口只读 discover 确认活动集合、私有回执及路径；漂移或未知归属阻止替换。提交推送 main 后用系统 skill-installer 的 install-skill-from-github.py，以 `--repo PennixRv/pennix-skills --ref <已核验提交> --method git --dest <新相邻暂存目录> --path <catalog 全部路径>` 完整暂存。路径和 Skill 名称来自该精确提交的 collection_contract，不另抄列表。

确认暂存树的 frontmatter、完整成员集合、来源和可执行模式后，从新暂存 lifecycle 入口执行 `replace-staged --component pennix-skills --staging <暂存> --destination <discover 的活动集合> --yes`。不把新 catalog 注入旧入口，不手改活动集合或收据。再次 discover/verify 检查事务完整性。若仅现行 profile 摘要因本次 catalog 过期，且所有原生安全与就绪条件满足，使用 `reconcile --component pennix-workflow-state --yes`；禁止重新 configure 或触碰秘密。

## 验证与回退

不新增简单版本断言测试；使用 JSON 解析、单字段结构差异审查及现有 test_lifecycle.py、test_managed_collection.py、test_skills_install.py。部署后核对源码与安装 catalog 一致、集合回执有效、cch-status scoped verify 通过。全量 verify 按实际结果记录无关阻塞，不扩展为其他组件升级。

回退对齐 CCH 0.1.45：在源码提交版本恢复，再从相应已推送提交按同一完整暂存/原生替换流程恢复集合；或使用已核验的旧完整集合按原生事务恢复。需要时按原生 reconcile 恢复摘要。失败时保留未知或第三方内容，不手工重写私有回执，不为了过门禁把新版本伪装为旧版本。
