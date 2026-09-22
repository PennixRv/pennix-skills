# 对齐 pennix-skills 与 Trellis beta

## Goal

在独立 pennix-skills 仓库中核验并收敛当前 Pennix Trellis beta 与 lifecycle catalog、相关 Skills、测试和发布元数据的兼容性。以 component-versions.json 为唯一版本源；只修复有当前根治理合同或可复现测试证明的差异；完成测试、提交推送 main、发布并验证安装产物。不得修改 Trellis/OpenViking、用户级 Codex 配置、凭据或无关历史任务。

## Requirements

1. 以 `skills/pennix-workflow-lifecycle/references/component-versions.json` 作为 Trellis lifecycle 版本的唯一静态来源。
2. 将已核验的 `trellis-cli` 目标更新为 `0.7.0-beta.7`，同步修正直接锁定旧值的测试。
3. 核对受 Trellis 影响的 Skills、脚本、adapter、测试和发布入口；仅修复有当前合同或可复现测试证据的差异。
4. 保持 Codex `$skill-installer` 的 Skills collection 所有权，不引入目标主机源码 checkout、第二套 catalog 或第二套安装器。
5. 在现有 `main` 上完成验证、提交和推送；没有现成的 npm/package release contract 时不虚构发布物。

## Acceptance Criteria

- [x] catalog 的 `trellis-cli` 目标为 `0.7.0-beta.7`，对应 npm 包可解析。
- [x] lifecycle 测试不再锁定 `0.6.43`，相关测试通过。
- [x] 兼容性矩阵覆盖 lifecycle、routing、decision-gates、handoff、doctor、collection、退役协议和发布元数据。
- [x] 产品源码未发现需要继续支持的退役协议或目标主机源码 checkout 入口。
- [x] `main` 已提交并推送；远端 `origin/main` 与本地提交一致。
- [x] 未创建额外发布物；仓库不存在既有 npm/package release contract 或 tags，Skills 仍由 `$skill-installer` 从 `main` 获取。

## Notes

- Delivery commit: `9ecb96b37671b5e700900a02e6de4a756188037a` (`fix: align Trellis catalog with beta.7`).
- `git ls-remote origin refs/heads/main` verified the same commit after push.
- The task uses the component repository's existing `main` directly; archive branch validation is skipped because no PR-backed branch exists.
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
