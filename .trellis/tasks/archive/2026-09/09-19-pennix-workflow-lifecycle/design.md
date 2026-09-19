# 设计：Pennix Workflow Lifecycle

## 边界

改动集中在 `skills/pennix-workflow-bootstrap` 的公开入口、其 catalog/adapter/fixture，以及 `skills/pennix-decision-gates`。不接管原生 package/plugin/submodule owner，不创建第二个 orchestrator 或状态 receipt。

## 最小模型

`component-versions.json` 同时保存组件的固定版本/source/template revision 和 action capability。入口从 catalog 枚举组件；每个 action 通过 capability 路由：`managed` 执行本地实现，`native-owner`/`verify-only`/`project-only` 不写入并输出 owner/下一步，`not-applicable` 明确说明不适用。

组合 submodule 由父仓库只固定 Gitlink/source/ref、clean checkout、子依赖和最终 Skill 物化；子仓库自己的 npm 版本、测试、发布和升级不复制到父 catalog。

## 行为

- `discover` 只读收集 host、scope、owner、source/template readiness 和 capability。
- `install/upgrade/uninstall` 保持单组件与 `--yes` 门槛；只对 `managed` 执行，已知 exact state 重复执行为 no-op，未知/漂移拒绝。
- `verify` 在 discover 基础上运行 catalog 声明的 template/source/postcondition 检查，不写状态。
- upstream 脚本/插件 ref 变化或 hash 不匹配时，在 owner command 前停止；项目初始化不从系统动作隐式触发。
- Skill 改名一次性迁移，不保留旧业务 alias；`seed-arch.sh` 可保留阶段语义，内部 `bootstrap.py` 改为 lifecycle 语义。

## 决策 gates

在现有 `pennix-decision-gates` 中加入 decision tree/frontier：先由仓库和来源回答事实，再按依赖拓扑每批询问 1–3 个互不影响的用户决策；交互后停止本轮，下一轮先回写当前 PRD/研究记录并重算 frontier。常规 Trellis brainstorm 单题合同不改，第三方 grilling 不作为运行时依赖。

## 明确不做

不加入批量 action、`plan/apply/rollback`、事务回滚、第三方 Skill vendor、用户级配置写入、真实安装/发布，或跨仓库源码修改。
