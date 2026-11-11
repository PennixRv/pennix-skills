# 实施清单：Pennix Workflow Lifecycle

1. 建立组件 catalog 的 capability/source/template contract，并让 discover、action 和 verify 共用它。
2. 将静态组件、Skills source/submodule、插件 ref 和 upstream hash 接入 catalog；移除入口层重复列表。
3. 迁移公开 Skill 和内部脚本命名，统一 README/AGENTS/routing/seed 输出，清理旧业务引用。
4. 补齐 managed template/Skills 的幂等、旧 managed state 升级、漂移拒绝、精确卸载和 postcondition 验证。
5. 对 native-owner、verify-only、project-only 组件补充可见拒绝/报告，并确保系统动作不创建项目资产。
6. 扩展 `pennix-decision-gates` 的依赖 frontier/批量提问/回写合同及最小静态测试。
7. 运行 Python 测试、`python -m compileall`、`bash -n`/zsh caller、`git diff --check`；只读检查改动范围后提交本仓库。

## 发布边界

本任务只提交 `pennix-skills` 源码和任务事实；是否发布、安装和根仓库集成验收由后续 owner 流程执行，不修改用户运行态。

## 实施结果

- 已将公开入口和文件树统一为 `pennix-workflow-lifecycle` / `lifecycle.py`，没有保留旧业务 Skill alias；同步更新 README、AGENTS、routing、seed 输出和模板标记。
- 已将组件能力、版本、来源、模板摘要、父仓库 submodule Gitlink、owner/scope 和项目初始化边界收敛到 `references/component-versions.json` schema 2；`discover`、五类生命周期 action 和 `verify` 共用 catalog。
- 已补齐 Arch 原生/WSL2 host 检查、managed/native-owner/project-only/verify-only 拒绝边界、静态模板漂移保护、Skills source/submodule/ref 校验、动态上游控制面与 SHA-256 变化阻断、安装副本幂等和嵌套符号链接漂移保护。
- 已在 `pennix-decision-gates` 加入依赖 frontier、分轮批量提问、决策回写和重算合同；保持 Trellis 普通单题流程，不引入第三方运行时依赖。
- 已通过生命周期 65 项测试、decision-gates 2 项测试、`compileall`、Bash/Zsh 语法检查和 `git diff --check`。
- 未执行真实系统安装、升级、卸载、发布或 `/home/penn/.codex` 写入；这些属于后续 owner/集成验收边界。
