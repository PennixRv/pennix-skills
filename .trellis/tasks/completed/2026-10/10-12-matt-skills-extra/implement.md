# Pennix 实施计划

1. 核对本仓库规范、源码/remote/干净基线和 FastCtx 已获批任务；绑定组件任务与任务分支。读取所有实际编辑目标、接口、调用方和测试。
2. 首先修订用户模板、总路由、FastCtx 与 Grill P0 规则；扩展已有契约测试，核验宿主真实调用面/Partial/Guarded 行为，更新生成摘要。P0 未通过不推进其他产品改动。
3. 把术语情境与决策地图方法融合到 Grill，把写作差集融合到既有参考；按根方法场景复核，不新增镜像测试。
4. 在 fork 完成十项精选并公开推送后，固定 catalog 来源/SHA/原始路径。泛化已有 collection resolver、目标/receipt、动作 owner 与安装适配器；补所有旧集合调用方。
5. 行为测试覆盖未知/重复/越界 catalog、受信 helper argv、部分下载、校验/切换/receipt 失败、已存在未知目标、来源/活动漂移、完整旧 SHA 升级/退回、同 SHA 幂等、独立卸载和另一集合不变。
6. 运行各 Skill 契约测试及 lifecycle 全量 `python3 -m unittest discover -s skills/pennix-component-lifecycle/tests -p 'test_*.py'`；完成跨文件审查、spec 判断与 diff 检查。按已授权批次提交并推送 `main`。
7. 隔离 CODEX_HOME 验证旧集合 staging/replace-staged、新集合 install/upgrade/verify/uninstall 与失败回滚。记录实际发现来源及真实触发证据，隔离不等于排除 user/admin/repo/plugin 来源。
8. 隔离通过后按原生生命周期更新本机两集合与用户模板；保留旧回退点。根任务记录最终 commit、精选 SHA、receipt、测试与宿主限制。逐项验收后原生归档和 journal，记录提交另批推送。

执行授权复用用户对根 revision 3 完整组件包的明确批准；不把该批准扩大为新方案、新项目或未列出的操作。新实质选择依原生 replan/seal/approval 合同处理。
