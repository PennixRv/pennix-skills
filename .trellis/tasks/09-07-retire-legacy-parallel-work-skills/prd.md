# 在 subnode adoption 后退役旧并行工作 Skill

## 目标

在已发布、可安装的 Trellis managed `subnode` 合同取代旧协议后，退役用户级 `parallel-work`、`evidence-report`、
`review-gate` 及其引用，使 `pennix-skills` 不再拥有 Channel lifecycle、terminal report transport、sandbox 指令或
subnode 报告协议。

## 要求

- 删除上述三个 Skill 的源码、脚本、references、tests、安装索引和所有路由引用；不保留兼容 wrapper。
- 保留 `trellis-research-record`，它服务一般 task research，不能被 subnode protocol 取代。
- 保留跨组件的 `pennix-workflow-routing`、检索、Hook、handoff、installer 与 diagnostics，但修正其旧 Skill 所有权
  描述，使其路由到项目选择的 Trellis workflow/Channel procedure。
- 更新安装器与 README/tests，使集合安装后不再声明或发现旧三个 Skill；安装行为仍只部署该私有集合，不创建 source
  checkout、改变 branch 或更新固定组件版本。
- 清理只能在 Trellis release、marketplace workflow 和至少一次可验证的 project adoption/host receipt 已具备后发生；
  若此前置失败，保持旧版本而非制造双协议。

## 非目标

- 不迁移或重写 `trellis-research-record`，不创建新的 user-level dispatcher Skill，也不将 Trellis managed assets
  复制进用户级目录。
- 不修改 fast-context submodule、用户 `AGENTS.md`、Trellis runtime、项目 workflow 或任何 session/runtime state。

## 验收标准

- [ ] repo 和 installation index 中不存在旧三个 Skill 或对其的可执行路由；保留的 Skill 不再声称管理 worker lifecycle。
- [ ] installer `--check` 和一次临时 destination install 验证 direct Skill structure 与 discovery layout。
- [ ] README/route tests 证明普通 task research 仍由 `trellis-research-record` 承担，项目并行 subnode 由 Trellis
  release + selected workflow 承担。
- [ ] source checkout 和 installed collection 都以已推送 commit/revision 可重现，未写入凭据/缓存/会话。

## 证据与依赖

- 总体设计：`codex-workflow-optimization/.trellis/tasks/09-07-trellis-reusable-concurrent-workflow-architecture/`。
- 本 task 仅在 Trellis release、marketplace revision 和 host/adoption evidence 就绪后激活；该顺序是正确性条件，
  不是可选优化。
