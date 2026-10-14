# 实施证据

- 新增 `pennix-project-agents-governance` 与 `pennix-codegraph-integration`，通过 routing 和集合清单发现；用户模板只增加批准的一行 CodeGraph 导航，整文件仍归 lifecycle 管理。
- 只读来源链 helper 检查用户与项目逐层候选、override/fallback、字节上限及受限条件，不声称证明宿主实际加载。4 项隔离测试通过。
- lifecycle 登记 Pennix Linux x64 npm 双包；只有精确核验的 `codegraph-bin 1.6.2-1` 可跨管理器替换，先检查 registry 候选，失败不重试包修改。相关测试纳入全量 179 项通过。
- routing 8 项测试通过；两个新 Skill 的 quick_validate 通过；中文文案检查通过。根侧最终离线集成 8/8 通过。
- Trellis 正文保留修复需要安装落点，清单目标同步为 `0.7.0-beta.50`；等待该双包和 CodeGraph `1.6.2-pennix.1` 实际发布后再部署。源提交、原生集合 staging/替换、用户模板与包迁移证据待续记。
