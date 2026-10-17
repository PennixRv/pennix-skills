# 补齐集合自描述与生命周期职责合同

## 目标（Goal）

随根任务用户扩围，核对并补齐集合自描述、同步/CI、Skill 路径发现、独立工具导航和活动文档/规范，解除集合与部署工具之间的错误依赖。当前已 replan，未批准本修订实施。

## 需求（Requirements）

- 集合 manifest 是成员、上游物化来源/提交、支持引用、命令和许可信息的唯一来源；本集合验证和同步/CI 不依赖已删除的 lifecycle catalog 或外部工具的可变配置。
- lifecycle Skill 只导航到独立 `pennix` 及固定 bootstrap，准确解释配置、URL＋Key、原生 owner 和卸载/数据边界；不复制执行器、部署模板、组件适配器或当前版本表。
- 通用首次加载规则属于用户 AGENTS 来源模板；workflow-routing 只解释跨组件的 Skill 身份/物理路径及别名映射、相对引用，不让 lifecycle Skill 承担首次加载前的规则。
- 修改评估使“尝试路径”“读取失败”“成功读取”分开；结构测试覆盖主/extra 集合及相对引用，不冻结中文句子，不把文字存在当作模型行为证明。
- README、AGENTS 手工正文、活动 spec、清理导航、同步/验证消费者一起收敛；归档历史不追溯改写，第三方物化快照只从真实来源同步。

## 验收标准（Acceptance Criteria）

- [ ] 独立 manifest、验证和同步/CI 可运行，不再引用旧 catalog/tests；部署工具只固定本集合提交和核验其合同。
- [ ] Skill 职责与独立工具一致，bootstrap 来自可取得的固定发行，Codex URL＋Key 不被错误引导为浏览器登录。
- [ ] routing 与评估覆盖宿主路径/别名、主/extra 集合、相对引用和失败读取；没有依赖中文原句的重复规则断言。
- [ ] 活动 README/AGENTS/spec/清理/CI/评估没有旧执行器入口；来源/引用/许可检查和适用回归通过，安装副本由根任务发布后原生刷新核验。

## 备注（Notes）

- 根任务：`/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-17-lifecycle-install-path-convergence`。具体跨仓库证据和完整方案在根任务，不复制源码或用户运行态。
- 当前未提交的路径规则与测试是待审草稿；它们不构成已验收实现。
