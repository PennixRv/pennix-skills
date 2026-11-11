# CCH0.1.44来源同步

direct/change-bearing；仅消费用户本轮明确授权的CCH显示修正发布。CCH owner实现，Pennix不复制renderer源码。

- CCH发布成功后在唯一`skills/pennix-workflow-lifecycle/references/component-versions.json`同步approved_version。CCH是native-owner，不给catalog新增安装ref。
- 既有生命周期单测确认固定来源一致，不新增版本表或deployment adapter。
- source提交推送，经system skill-installer保持mode安装全部catalog entries到唯一staging；验证后由staged原生replace-staged替换。
- 从新installed入口discover；升级由CCH native-owner执行（catalog不接受managed upgrade），再scoped verify，确认managed runtime同步0.1.44和source parity，用户凭据/外文保留。
- 清理本轮staging和安装备份，owner任务归档journal。没有其他组件升级、用户偏好或配置变化。
