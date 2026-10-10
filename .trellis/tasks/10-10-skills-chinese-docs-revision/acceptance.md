# 交付与安装验收

## 来源与测试

- Grok 来源：`PennixRv/grok-search`，提交 `1af50d6e049d5349cbd44d1f398ea016bd70a37a` 已推送 main。集合沿原 archive 范围交付 48 个文件，字节和执行模式一致；3 份来源任务记录不复制到 Skill 消费者。
- Windsurf 来源：`PennixRv/windsurf-code-search`，产品提交 `3e87626`，含归档与原生日志的来源提交 `ff4c2e2a4432e13cc0a19155a8178c792af57375` 已推送 main。18 个 npm-pack 文件集合一致，package.json 按原生 consumerManifest 规范化；其键名未翻译。
- 来源精确提交写入唯一 catalog 的原 ref/commit 字段。两个 CLI 运行机制和版本未变，文案通过来源提交和集合安装交付，没有无关二进制发布。
- 12 入口、15 已有参考、7 界面与新增写作参考的复核见 `semantic-review.md`；现有测试合计 232 项 Python、114 项 Windsurf、7 组 Grok 通过。根离线集成 8 项通过。
- 用户规则旧完整模板 SHA 为 `57eda055881bdd719bd9e72e9d94e009d74b99beac20fc55687b22974689268d`，新模板 SHA 为 `a126ddcab9cef58a2fdc70d827d079accf28df3f10ede25df3d5c40e80687a58`，已核验真实旧模板显式升级、重复幂等和未知内容保留。

## 部署前记录

产品提交推送后，从系统安装器固定产品提交并按 catalog 全路径安装到新 staging；校验后使用同版原生 replace-staged，再显式 upgrade codex-agents。实际完成与清理结果在后续记录中追加，不以离线测试冒充已安装。

## 实际安装与清理

- 集合产品提交 `d7bb1852a81bfd595631b96f39918fcb7468dd89` 已推送 main。系统 skill-installer 使用该精确 ref、catalog 的全部 12 路径及 git 模式，在新同级 staging 安装。校验完整成员集、frontmatter、141 文件逐字节相等和 seed 执行权限后，从 staging 的同版 lifecycle 原生 replace-staged，返回 changed。
- 使用新安装入口显式 upgrade codex-agents，返回 changed；实际用户文件从已知旧完整模板迁移至新模板。新文件与来源模板字节相等，SHA 为 `a126ddcab9cef58a2fdc70d827d079accf28df3f10ede25df3d5c40e80687a58`，没有非空 AGENTS.override.md 遮蔽。
- 原生 verify --component pennix-skills --yes 与 verify --component codex-agents --yes 均退出 0；scope=component、status=match、failures/advisories 为空。集合 integrity、规则 current/active、Grok 命令映射及 PATH 核验通过。
- 安装后 141 个受跟踪文件与产品提交的内容和执行权限一致；没有本轮 staging 候选。生命周期规定的 Grok 运行依赖由原生安装后动作生成，不提交源码或根仓库。
- 三份原文核对临时副本和 apply_patch 探针经确认内容后精确删除；测试与安装的暂存由各自原生流程清理。历史任务、许可及既有发布证据保留，无新 .new 候选。
- discover 同时报告本轮无关的 tmux 3.8 与固定 3.7c 不同，以及未启用的 Grok 配置目标 drifted；这不是本轮改动目标，未更改包或凭据，也不宣称全工作流基线通过。

产品交付和当前主机安装已验收；后续提交只补本任务证据、原生归档和日志，Skill 产品文件保持该已安装提交内容。
