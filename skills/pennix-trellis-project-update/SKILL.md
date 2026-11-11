---
name: pennix-trellis-project-update
description: "通过当前原生 Trellis CLI 安全更新已管理项目的生成资产和明确选定的工作流；用户要求升级项目 Trellis 资产或工作流时使用，不用于系统组件部署或只读诊断。"
---
# Trellis 项目更新
用于已经初始化 Trellis 的项目。项目根目录必须明确。项目资产生成和冲突分类只能由原生 `trellis` CLI 负责。
## 归属

- 全局组件安装、配置、集合替换或核验使用 `$pennix-component-lifecycle`。
- 只读本地诊断使用 `pennix-trellis-asset-check`。
- 已有项目的 Trellis 更新和选定工作流刷新使用本 Skill。不要从 Trellis 检出目录复制文件，也不要创建第二个更新器。
- 明确授权的项目初始化、重初始化或移除，以及跨 owner 的 AGENTS 操作编排交 `$pennix-project-agents-governance`；本 Skill 保留已管理 Trellis 资产更新职责。不要为单个缺块改用整次 `init --force`，AGENTS 的块级保护不代表其他生成资产不会被覆盖。
- Trellis 任务、Teamwork、交接、Hook 和平台原生协议保留各自原生归属；执行载体不模拟或接管状态机。

## 预检

在明确的项目根目录执行：

1. 读取最近的 `AGENTS.md`、`.trellis/workflow.md`、`.trellis/config.yaml`、`.trellis/.version` 和 `.trellis/.template-hashes.json`。如果还存在旧的 `.trellis/workflow-provenance.json`，只将其作为历史残留核对；当前 bundled native workflow 的来源与完整性由 Trellis CLI 的版本和模板哈希管理。
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

它允许当前 fork 更新安全文件和新增模板文件，并为已修改模板写入 `.new` 候选。逐个按当前已授权合同审查候选。只有当前方案明确选择保留全部已修改文件而不生成候选时，才使用 `--skip-all`：

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

显式 custom workflow source 只有在用户明确选择时才参与。需要可复现结果时，应使用不可变引用（通常为提交 SHA）；分支名适合用户自行管理的可变来源，不应被误当作发布锁定。先预览候选，不直接替换活动工作流：

```bash
trellis workflow --list --workflow-source 'gh:OWNER/REPO/path#REF'
trellis workflow --template TEMPLATE_ID \
  --workflow-source 'gh:OWNER/REPO/path#REF' \
  --create-new
```

明确的 `trellis workflow --create-new` 始终写入 `.trellis/workflow.md.new`，即使活动工作流与此前来源完全相同；它不会更新活动工作流。这与 `trellis update --create-new` 写入的冲突候选不同。审查整个候选，记录接受结果，再用相同的模板和来源应用。只有任务明确授权且活动文件被标记为 modified 时才使用 `--force`。

应用后先核对当前选定来源。仅 bundled native 使用以下原生复核：

```bash
trellis workflow --list
trellis workflow --template native
```

对 bundled native，`trellis workflow --template native` 会将活动文件与 CLI 内置模板比较；内容一致时刷新模板哈希，存在本地修改时停止并要求显式处置。对 custom source，保留其显式来源和用户管理边界，不把它悄悄切换为 bundled native 或保存的本地变体。

custom source 使用已接受的相同 TEMPLATE_ID、显式 source 和不可变 REF 复核；必要时重新生成 `.new` 候选并比较，不能运行上面的 native 切换命令代替校验。

对 `trellis update --create-new` 候选，逐个决定精确的 `.new` 路径。保留所有待处理或不相同的候选。活动文件已接受且任务已记录处置后，只能删除与活动文件逐字相同的 sidecar：

```bash
test -f PATH.new && test ! -L PATH.new && cmp -s -- PATH PATH.new && rm -- PATH.new
```

删除不同的 sidecar 必须有精确的拒绝记录和授权。不得使用宽泛的 `find ... -delete`、递归清理或未审查命令删除 `.new` 文件。

当前 bundled native workflow 采用五阶段路线。trellis teammates 按主会话的只读工作包返回报告；paseo delegated-agent 仅在已授权实施阶段执行完整工作包，由主会话集成和接受。不使用宿主原生子代理或独立 CLI 启动路径恢复旧执行模型，历史记录和恢复摘要不扩大授权。

## 完成核验

处理完每个预期候选后：

1. 重新运行 `trellis update --dry-run`；工作流发生变化时，运行 `trellis workflow --list`，并对 bundled native 运行 `trellis workflow --template native` 复核活动文件与模板哈希。
2. 运行 `git diff --check` 和项目相关测试、lint 或类型检查。
3. 检查 `git status` 和完整差异。只能留下请求范围内的项目资产和持久化任务证据；每个 `.new` 候选都必须已接受、明确拒绝或作为有解释的待处理项保留。
4. 确认 `.trellis/.version` 和原生模板哈希仅由 Trellis 修改，项目差异中没有秘密、会话、缓存、运行态或源代码检出目录。

原生命令失败、来源缺失、已修改文件需要尚未授权的覆盖决定或核验不完整时，返回受影响阶段或决策入口。不要猜测、强制操作或声称完成。
