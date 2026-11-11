# 组件实施计划

1. 由根侧展示完整方案，取得明确答复后，本任务原生 seal／approve／start；编辑前加载 before-dev 和本仓库适用规范。工作分支 main，与当前既有维护方式一致。
2. 读取 catalog schema、所有受影响 probe／operation 调用和现有 npm／集合测试；最小增加 pnpm 条目，更新 Ponytail 版本与 Marketplace 发布 ref、AoE 版本。补 catalog 合同检查，不改变 npm 默认 prefix 配置逻辑。
3. 在现有集合 adapter 和 CLI 实现默认预览的 `discard-staged`，加执行摘要参数；复用安全路径及集合校验，单独覆盖完整待删树摘要。补真实临时目录测试：有效成员子集、只读预览、精确删除、活动树／收据／命令保留、越界／链接／异常 owner／非集合顶层文件、缺少摘要／内容或缓存变化／根目录替换的拒绝路径及删除失败回执。核验宿主符号链接攻击防护及非事务限制，不增加自动重试或全局清理。
4. 同步 lifecycle Skill、resource-cleanup 及资源策略中的最少必要入口说明。运行全部 lifecycle 测试、受影响 Skill 合同和 frontmatter 校验、文案及 diff 检查；审查未知目录处理没有削弱默认 discover／安装／卸载保护。
5. 提交推送组件；系统 skill-installer 以精确提交把完整 catalog 集合装入新的相邻暂存，核验执行位和集合后用新入口 replace，确认安装 verify 为 match。只在组件内容变化时更新集合，不回退后续已交付内容。
6. lifecycle 按固定版本升级／安装 pnpm 到 `$HOME/.local`，核验 pnpm／pnpx、owner、PATH 优先和 Trellis 的 10.32.1 冻结锁文件实际调用，再确认旧 `/usr` 副本按原有 npm 迁移逻辑移除。对 Ponytail 通过原生 Marketplace 接口切换发布 ref，回读安装／启用／版本和已安装 Skill／Hook 资产；AoE 用 scoped verify。
7. 新入口对本次精确 stage dry-run，验证输出和实际内容边界，再用同一摘要执行已批准丢弃；回读目标不存在、活动集合／收据／命令核验一致，记录实际执行及文件字节。若目录发生变化或安全形状不符，停止，不扩大范围或静默忽略。
8. 分别 scoped verify 后执行完整 `verify --yes`，由根侧运行离线组合验收。所有要求均有实际证据后提交实施记录，原生归档与 add_session，推送本组件；根侧固定最终提交并独立归档。

## 验收与回退入口

使用现有 `python3 -m unittest discover -s skills/pennix-component-lifecycle/tests` 和新增的暂存行为测试，按当前 Skill 合同检查入口验证文案。完整验证与真实安装、来源和删除回执缺一不可；合同／夹具通过不能替代实机结果。

原始 pnpm 安装是 npm `/usr` 中的 10.32.1，目标仍为同版本；只通过 npm 恢复或移除。Ponytail 来源基线为原生 list 所记录的 Git URL、已启用版本和 Marketplace HEAD；原生切换失败先观察实际状态，不手工 checkout 缓存。集合回退从前一已验收提交重新暂存并 replace。stage 删除没有自动回退，预览和摘要门禁必须先通过。
