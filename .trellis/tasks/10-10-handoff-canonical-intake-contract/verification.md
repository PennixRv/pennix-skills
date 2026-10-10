# 组件验证记录

## 实施范围

交付对象是 `skills/pennix-session-handoff/` 及其当前 backend quality contract。schema 10 统一使用核心视图必读、历史按需；schema 8/9 只读。完整公开历史只存于 `conversation`，共享校验器验证所有消费字段与引用，新增只读 `read` 接口按 Unicode 字符分页，不写游标或改变 handoff 生命周期。admission 在既有收据中保存真实 history 范围。

## 结果

- handoff 两个测试模块：33 项通过，涵盖受控拒绝、跨入口校验、Unicode 无损分页、历史引用边界、schema 8/9 只读以及生命周期不变性。
- 与最终变更一致的组件 CI：按仓库 `.github/workflows/verify.yml` 执行全部 19 个 Python Skill 测试模块，205 项通过。两条 `permission denied` 输出是配置迁移测试刻意验证的失败场景，对应断言通过。
- Skill Creator `quick_validate.py`：有效。
- 当前 catalog 的 `validate_staged_collection`：通过，集合源为 `skills/`。
- 组件 `task.py validate 10-10-handoff-canonical-intake-contract`：通过。
- `git diff --check`：通过。
- 根 `node scripts/run-workflow-integration.mjs --offline --pretty`：8 项通过，0 failed/blocked/not_run。
- 原始 handoff 样本仅在内存移除重复投影并改投 schema 10 验证：返回 `ready`。序列化大小估算由 44,856,743 bytes 降至 21,384,395 bytes（52.3%）；样本原始 SHA-256 前后相同。

## 交付边界

尚未包含源提交/推送、系统 staging 安装与 scoped verify、根侧固定产品提交和原生归档。这些在 `deployment.md` 及根任务 acceptance 中记录实际结果。
