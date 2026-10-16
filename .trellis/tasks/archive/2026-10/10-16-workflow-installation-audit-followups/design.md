# 组件设计

## 复用现有架构

pnpm 按 catalog 既有 npm package 结构登记，固定 10.32.1 和精确 tag，prefix／install_owner 沿用用户级安装合同。`npm_previous_locations`、`component_operation` 与 host 包命令继续负责安装、验证后移除旧 prefix；不复制迁移逻辑。Ponytail 和 AoE 只修订有当前证据的 pin／ref，保留原生 owner。

Ponytail 使用 Codex 已声明的 marketplace remove／add --ref，再回读 list；原生 plugin add 不提供 ref，不能编造 upgrade 子命令或把固定 Marketplace 等同于固定上游插件下载提交。现有 5.3.1 插件若保持安装与启用就不重复卸载；若原生操作确实需要恢复安装，仅用 plugin add，并以真实版本、来源和发布资产核对结果验收。遇到超出方案的版本或来源变化，停止相关动作并保存回执。

## 最小暂存丢弃接口

在既有 CLI 增加 `discard-staged --component pennix-skills --staging <精确路径>`，无 `--yes` 时只预览；执行增加 `--yes --expected-digest <预览摘要>`。校验和动作放在既有集合 adapter，CLI 只编排和输出，不新增通用清理框架。

复用安全路径和集合 frontmatter 检查：目标必须为当前所选 Codex home 的 skills 的直接子目录，名称属于本集合暂存名称；明确拒绝活动目录、收据、其他集合、兄弟目录、路径别名和符号链接。只允许合法 catalog 成员子集，检查当前用户 owner、目录／普通文件和安全树形；非集合顶层内容拒绝。删除摘要覆盖根目录身份、所有条目身份／模式／owner 及文件内容，包括 Python 缓存；不直接复用会忽略缓存的 `collection_digest`，也不改变活动集合摘要合同。预览统计路径、条目和文件字节，不输出正文或秘密。

执行前重新核验类型、owner、安全形状和摘要，缺少或不匹配的 expected-digest 不写入；已检测到根目录替换或内容变化就停止。不通过 force、前缀展开或修改收据继续。采用宿主可抵御符号链接替换的原生目录删除，缺少该能力时阻断；核验与删除仍非文件系统事务，不能保证拦截所有并发写入，原生删除失败也可能留下部分目录，须报告完整错误和剩余现场。当前用户明确批准的精确丢弃范围不等于接纳或证明原始来源。

discover 的 unknown staging 行为及私有收据合同保持。Skill 和资源策略只增加显式调用新入口的条件及结果边界。其他集合、自动清理、年龄／PID 猜测、无关系统资源均不进入实现。

## 安装、风险与回退

完整集合经当前系统 skill-installer 从已推送精确提交暂存，由暂存版 lifecycle replace；不使用或覆盖本次待丢弃的旧目录。新入口验收前不删除旧 stage。

pnpm 在目标已核验后才卸载旧 prefix，回退仍通过 npm 同版本安装；Ponytail 原生来源切换前保存原生 JSON 和当前发布／版本信息，失败按真实状态使用原生接口恢复，不写缓存。AoE 不改二进制。集合通过上一已验收源码提交重新安装回退，不修改收据。stage 的已批准实际丢弃不可自动恢复，必须有真实预览和同一摘要。

不引入 npm 发布或 Trellis 版本更新；最终源码提交与安装资产、实机结果和根侧集成共同构成验收。
