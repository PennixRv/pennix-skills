# 工作流 npm 安装落点与 lifecycle 治理实施计划

1. 读取当前源仓库状态和所有 npm/package/prefix/owner 调用方，保留既有未相关改动；运行 catalog 和基线测试。
2. 修改 catalog 与 schema 校验，加入 `$HOME/.local` npm prefix、用户 owner、Paseo 固定版本和最小受控脚本白名单。
3. 修改 host 命令构造和 lifecycle：多 prefix inventory、目标入口探针、owner/PATH 报告、用户 prefix 安装，以及目标安装验证成功后才清理旧副本。
4. 为多 root、系统旧包、用户目标包、owner 漂移、失败保留旧路径和 Paseo 脚本白名单补充有意义的夹具测试。
5. 运行 lifecycle 专属 unittest、catalog/discover/verify 离线检查和中文文档检查；修复组件范围内的机械问题。
6. 更新源侧任务记录，提交 `pennix-skills`，推送当前维护分支并快进 `main`（沿源仓库既有合同）；记录精确提交。
7. 回到根任务，依据精确源提交完成暂存接纳和 `$HOME/.local` 迁移；Trellis、FastCtx、CodeGraph、CCH 先行，Paseo 最后重装/重启并验证重连。

## 回滚

源码回滚使用上一个已验收提交；运行态迁移失败时保留旧 npm prefix，恢复 PATH/调用方并由原生 owner 恢复旧入口。不得用 shim 掩盖失败，也不得删除 AUR 包、项目依赖、凭据或 Paseo daemon 数据。

## Revision 2：最小补充

1. 只在现有 `component_operation` 的用户级 npm 安装/升级路径接入默认 prefix 规范逻辑，目标取 catalog，使用 npm 原生用户级设置和回读；已经匹配的包也覆盖，配置失败不得继续安装或清理旧包。
2. 在 `SKILL.md` 现有 npm 合同段落明确说明用户默认 prefix 副作用及边界；不增加组件、命令、profile 字段或收据。
3. 在现有 lifecycle 测试中覆盖配置幂等、前置失败、包已匹配、写入/回读失败阻断及无关 npm 配置保留；验证只读、卸载和非 npm 流程不写配置。
4. 运行 lifecycle unittest、编译、中文文案与差异检查；提交推送 `main`，由根任务原生重新接纳和验证活动入口，随后归档组件任务并记录会话。
