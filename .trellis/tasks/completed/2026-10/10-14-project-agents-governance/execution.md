# 实施证据

- 新增 `pennix-project-agents-governance` 与 `pennix-codegraph-integration`，通过 routing 和集合清单发现；用户模板只增加批准的一行 CodeGraph 导航，整文件仍归 lifecycle 管理。
- 只读来源链 helper 检查用户与项目逐层候选、override/fallback、字节上限及受限条件，不声称证明宿主实际加载。4 项隔离测试通过。
- lifecycle 登记 Pennix Linux x64 npm 双包；只有精确核验的 `codegraph-bin 1.6.2-1` 可跨管理器替换，先检查 registry 候选，失败不重试包修改。相关测试纳入全量 179 项通过。
- routing 8 项测试通过；两个新 Skill 的 quick_validate 通过；中文文案检查通过。根侧最终离线集成 8/8 通过。
- Trellis 正文保留修复需要安装落点，清单目标同步为 `0.7.0-beta.50`；等待该双包和 CodeGraph `1.6.2-pennix.1` 实际发布后再部署。源提交、原生集合 staging/替换、用户模板与包迁移证据待续记。

## 最终源交付与部署

- 源提交 `14171919d1003b7042ef4e1dc503959b05672065` 已推送 `codex/project-agents-governance` 和 `main`。新增的项目 AGENTS 治理 Skill、CodeGraph 集成 Skill、来源链只读 helper、routing、集合清单和 lifecycle 精确迁移合同均来自该提交。
- lifecycle 全量测试为 `179 passed`；routing 8 项、helper 4 项、两个 Skill quick validation、catalog 加载和中文文案检查均通过。集合通过原生 skill-installer staging 后由 lifecycle `replace-staged` 成功替换，post discover/verify 的 failures 为空。
- 用户模板通过 `codex-agents` 原生 upgrade 更新；Trellis CLI 通过 lifecycle 更新为 `0.7.0-beta.50`；CodeGraph 通过精确的 `codegraph-bin 1.6.2-1` owner/version 预检后完成 npm fork 双包迁移，post verify 通过。没有初始化根项目 CodeGraph 或改写用户级 Codex 配置。
- 根侧最终离线组合检查为 8/8 passed。项目治理 Skill 保留静态候选与真实宿主加载的区分；CodeGraph 实际 MCP smoke 由已发布版本完成，宿主内部加载追踪不可见的限制仍按报告保留。
