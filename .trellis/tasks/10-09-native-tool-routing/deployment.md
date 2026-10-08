# 发布、安装与关联资产验收

- Skills 发布：`PennixRv/pennix-skills` 的 `main`，修复提交 `c959eec51d210a7ea6d41171d077b8b7b917a72b`，已推送 GitHub；本集合按 Git 提交发布，没有单独 npm 版本。
- 系统 skill-installer 从该明确提交以 `--method git` 按唯一 catalog 的 11 个 paths 安装到同级 staging。staging 名称/结构、变更文件字节一致性和 seed 可执行模式均通过。
- 仍安装的旧 lifecycle 精确卸载旧 codex-agents 受管块；从 staging 调原生 replace-staged 替换完整 collection，然后新 lifecycle 安装新块。未手编辑安装树、receipt 或模板哈希。
- 原生 component-scoped verify：pennix-skills 为 match / collection_integrity=match / failures=[]；codex-agents 为 match / agents_template=current / failures=[]。
- 安装副本的两份路由 Skill、AGENTS 模板和 catalog 与修复源字节一致；template revision 与实际 SHA-256 一致。
- 用户 AGENTS 受管块以外内容的规范化 SHA-256 不变；用户 config.toml / hooks.json SHA-256 不变；auth.json 的大小、修改时间、权限不变，未读取或保存其正文。
- 本仓库关联 Trellis 资产通过原生 dry-run/update --create-new 更新至 0.7.0-beta.41，只自动更新 4 个未被用户改写的模板及原生元数据。复核 dry-run 为 Already up to date。任务、spec 和当前会话绑定保留。
- 本轮 staging 已由事务替换消费；本轮 update 自动备份 `.trellis/.backup-2026-10-08T23-54-53` 已在验证后移除；没有本轮 .new 或源码临时目录。未删除任务前已有的备份。
- 根侧只读组合门禁 8/8 passed，failed/blocked 为零。
- Trellis 正确原生路径无缺口，不发布冗余身份兼容补丁；既有 identity preservation 修复为 `60de8057`（首个含该修复的 beta tag 为 .25），当前安装 .41 已包含。FastCtx 维持 0.2.21。
- 收尾提交中的关联 Trellis 物化和任务记录不改变此次已安装的 Skill 内容；安装版本以修复提交及 collection receipt 为准。

## 完成与验证限制

当前 task 的五项验收均已满足，计划文档保持封口时内容，验收状态在本文件记录。历史语义写入误用仍未证实，不抹掉该证据边界。没有独立子节点或运行时强制拦截测试；提示词不能保证模型永不偏离。全组件 discovery 中已有的 SiYuan readiness blocked、Ponytail 版本漂移等不属于两项路由缺口，未修改；本轮安装验收是两个明确 component 的定向验收。

