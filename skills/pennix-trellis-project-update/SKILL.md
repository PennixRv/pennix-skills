---
name: pennix-trellis-project-update
description: "通过当前原生 Trellis CLI 安全更新已管理项目的生成资产和明确选定的工作流；用户要求升级项目 Trellis 资产或工作流时使用，不用于系统组件部署或只读诊断。"
---
# Trellis 项目更新
用于已经初始化 Trellis 的项目。项目根目录必须明确。项目资产生成和冲突分类只能由原生 `trellis` CLI 负责。
## 归属

- 全局组件安装、配置、集合替换或核验使用 `$pennix-workflow-lifecycle`。
- 只读本地诊断使用 `workflow-doctor`。
- 已有项目的 Trellis 更新和选定工作流刷新使用本 Skill。不要从 Trellis 检出目录复制文件，也不要创建第二个更新器。
- Trellis 任务、Channel、交接、Hook 和平台原生协议保留各自原生归属。不要用脚本或 FastCtx 状态机模拟它们。

## 预检

在明确的项目根目录执行：

1. 读取最近的 `AGENTS.md`、`.trellis/workflow.md`、`.trellis/config.yaml`、`.trellis/.version`、`.trellis/.template-hashes.json`，以及存在时的 `.trellis/workflow-provenance.json`。
2. 确认存在 `.trellis/`。不存在时停止并使用原生 Trellis 初始化流程；本 Skill 不把初始化作为更新副作用。
3. 运行 `trellis --version`、`trellis platforms` 和：

```bash
trellis update --dry-run
```

4. 在活动 Trellis 任务中记录当前选定工作流、任务或仓库归属和精确更新范围。若请求改变工作流来源、模板、迁移或覆盖策略，实施前使用 `$pennix-decision-grill` 并持久化决策。

## Trellis 资产更新

使用原生更新命令。可重入且不破坏现有内容的路径是：

```bash
trellis update --create-new
```

它允许当前 fork 更新安全文件和新增模板文件，并为已修改模板写入 `.new` 候选。逐个按项目合同审查候选。只有封口任务明确选择保留全部已修改文件而不生成候选时，才允许使用 `--skip-all`：

```bash
trellis update --skip-all
```

不要默认使用 `--force`；只有活动任务点名了精确文件和决策时才使用。只有验收明确包含原生迁移时才使用 `--migrate`，因为迁移可能重命名或删除弃用文件。不得手改 `.trellis/.template-hashes.json` 来消除冲突。

通用更新期间保留以下项目或运行态内容：`.trellis/spec/`、`.trellis/tasks/`、`.trellis/workspace/`、`.trellis/.runtime/`、凭据、缓存、日志、数据库和无关用户文件。由原生 Trellis 决定哪些受管平台文件及根目录受管块可以安全刷新。

## 工作流刷新

工作流选择独立于 `trellis update`。先发现模板：

```bash
trellis workflow --list
```

Marketplace 内容在获取或写入前必须同时具备模板 ID、明确来源和不可变引用（通常为提交 SHA）。分支名或当前文件内容不足以构成来源。先预览候选，不直接替换活动工作流：

```bash
trellis workflow --list --marketplace 'gh:OWNER/REPO/path#IMMUTABLE_REF'
trellis workflow --template TEMPLATE_ID \
  --marketplace 'gh:OWNER/REPO/path#IMMUTABLE_REF' \
  --create-new
```

明确的 `trellis workflow --create-new` 始终写入 `.trellis/workflow.md.new`，即使活动工作流与此前来源完全相同；它不会更新活动工作流或来源记录。这与 `trellis update --create-new` 写入的冲突候选不同。`modified` 也可能由来源或引用变化，或比较基线变化导致，不能单凭它判断消费者文件被人修改。核对来源、提交和内容后再作结论。审查整个候选，记录接受结果，再用相同的模板、来源和引用应用。只有任务明确授权且活动文件被标记为 modified 时才使用 `--force`。

应用后运行：

```bash
trellis workflow --verify
```

该命令核对已记录的工作流 ID、来源、引用、内容哈希和活动文件内容。缺少来源记录时，不得仅凭文件内容相同来修复；应通过原生命令选择精确来源并物化，或记录旧状态不可核验并停止。不得在 `native`、Marketplace 模板和保存的本地变体之间悄悄切换。

对 `trellis update --create-new` 候选，逐个决定精确的 `.new` 路径。保留所有待处理或不相同的候选。活动文件已接受且任务已记录处置后，只能删除与活动文件逐字相同的 sidecar：

```bash
test -f PATH.new && test ! -L PATH.new && cmp -s -- PATH PATH.new && rm -- PATH.new
```

删除不同的 sidecar 必须有精确的拒绝记录和授权。不得使用宽泛的 `find ... -delete`、递归清理或未审查命令删除 `.new` 文件。

当前 `codex-subnode-channel` 工作流默认由主会话内联交付；只有明确要求的独立证据才使用子节点，持久化报告仍须由协调代理核验并接受。

## 完成核验

处理完每个预期候选后：

1. 重新运行 `trellis update --dry-run`；工作流发生变化时，针对持久化的不可变来源运行 `trellis workflow --verify`。
2. 运行 `git diff --check` 和项目相关测试、lint 或类型检查。
3. 检查 `git status` 和完整差异。只能留下请求范围内的项目资产和持久化任务证据；每个 `.new` 候选都必须已接受、明确拒绝或作为有解释的待处理项保留。
4. 确认 `.trellis/.version` 和原生模板哈希仅由 Trellis 修改，项目差异中没有秘密、会话、缓存、运行态或源代码检出目录。

原生命令失败、来源缺失、已修改文件需要未封口覆盖决策或核验不完整时，返回规划或决策门禁。不要猜测、强制操作或声称完成。
