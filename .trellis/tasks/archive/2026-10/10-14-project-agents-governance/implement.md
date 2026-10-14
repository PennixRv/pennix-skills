# 实施与检查

1. 检查现有 routing、lifecycle catalog/adapters/collection、用户模板和 Codex 静态探针及调用方。
2. 写两个简短 Skill、必要参考及最小来源链 helper，覆盖边界行为；关联 routing/集合/README。
3. 增加 fork npm 来源及精确 AUR 迁移合同和测试；源模板增加一行导航。
4. 运行 lifecycle/routing/helper tests、Skill quick_validate 和中文检查；固定源提交后原生 staging/部署，不手写安装副本。
5. 在双包发布成功后执行明确授权的迁移，验证 owner/PATH/MCP/upgrade、模板整文件和 Skills 发现路径；回写 execution.md 和根侧精确版本。

部署失败保存当前包、配置、索引与回执；不自动清理、重建索引或再次改包。
