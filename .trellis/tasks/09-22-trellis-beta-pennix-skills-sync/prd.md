# 对齐 pennix-skills 与 Trellis beta

## Goal

在独立 pennix-skills 仓库中核验并收敛当前 Pennix Trellis beta 与 lifecycle catalog、相关 Skills、测试和发布元数据的兼容性。以 component-versions.json 为唯一版本源；只修复有当前根治理合同或可复现测试证明的差异；完成测试、提交推送 main、发布并验证安装产物。不得修改 Trellis/OpenViking、用户级 Codex 配置、凭据或无关历史任务。

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
# 对齐 `pennix-skills` 与 Trellis beta

## Goal

让 lifecycle catalog 和相关用户级 Skills 与当前 Pennix Trellis beta 及项目工作流合同一致，保证发现、安装、升级、卸载和验证使用正确的 Trellis 目标。

## Confirmed Facts

- 根集成合同固定 `@pennixrv/trellis@0.7.0-beta.7` 与 `@pennixrv/trellis-core@0.7.0-beta.7`。
- 当前组件 `main` 为 `0c1aa46`，工作树干净。
- `skills/pennix-workflow-lifecycle/references/component-versions.json` 将 `trellis-cli` 固定为 `0.6.43`；`tests/test_lifecycle.py` 对该旧值有直接断言。
- npm registry 当前可解析 `@pennixrv/trellis@0.7.0-beta.7` 和 `@pennixrv/trellis-core@0.7.0-beta.7`，因此不是不存在的候选版本。
- 组件现有 lifecycle、routing、decision-gates、handoff 和 doctor 文本已声明不复制 Trellis runtime 或 task/channel 协议；产品源码中的退役协议引用必须继续通过检索确认，历史任务文件不属于产品入口。

## Requirements

1. 以 `component-versions.json` 作为唯一版本源，更新已验证的 Trellis catalog target。
2. 更新直接断言旧 target 的 lifecycle 测试，并保持 catalog schema 与所有 action 校验不变。
3. 审查相关 Skill、adapter、脚本和文档；只有存在可复现的 beta 语义不一致时才修改。
4. 保持 Skills collection 由 Codex `$skill-installer` 拥有，目标主机不需要 Pennix source checkout；不新增安装器或第二份 catalog。
5. 完成现有测试、diff review、提交并推送 `main`；若仓库发布约定要求，发布对应版本并验证可安装结果。

## Acceptance Criteria

- [x] catalog 的 `trellis-cli` target 为 `0.7.0-beta.7`，npm registry 可解析该版本。
- [x] lifecycle 测试不再锁定 `0.6.43`，catalog/lifecycle/collection 相关测试通过。
- [x] 产品 Skill、脚本和 README 没有需要继续支持的退役协议或目标主机 source-checkout 部署入口。
- [x] 没有重复版本表、凭据、运行时状态或无关历史任务变更。
- [ ] `main` 上提交、推送和发布/安装验证结果可复现并记录在任务中。

## Out Of Scope

- 修改 Trellis、Marketplace、OpenViking 或 `/home/penn/.codex`。
- 迁移、归档或修复其他历史任务。
- 改变 lifecycle 的既有宿主边界、卸载安全边界或原生 owner 所有权。
