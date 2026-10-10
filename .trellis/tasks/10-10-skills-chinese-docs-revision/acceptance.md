# 交付与安装验收

## 来源与测试

- Grok 来源：`PennixRv/grok-search`，提交 `1af50d6e049d5349cbd44d1f398ea016bd70a37a` 已推送 main。集合沿原 archive 范围交付 48 个文件，字节和执行模式一致；3 份来源任务记录不复制到 Skill 消费者。
- Windsurf 来源：`PennixRv/windsurf-code-search`，产品提交 `3e87626`，含归档与原生日志的来源提交 `ff4c2e2a4432e13cc0a19155a8178c792af57375` 已推送 main。18 个 npm-pack 文件集合一致，package.json 按原生 consumerManifest 规范化；其键名未翻译。
- 来源精确提交写入唯一 catalog 的原 ref/commit 字段。两个 CLI 运行机制和版本未变，文案通过来源提交和集合安装交付，没有无关二进制发布。
- 12 入口、15 已有参考、7 界面与新增写作参考的复核见 `semantic-review.md`；现有测试合计 232 项 Python、114 项 Windsurf、7 组 Grok 通过。根离线集成 8 项通过。
- 用户规则旧完整模板 SHA 为 `57eda055881bdd719bd9e72e9d94e009d74b99beac20fc55687b22974689268d`，新模板 SHA 为 `a126ddcab9cef58a2fdc70d827d079accf28df3f10ede25df3d5c40e80687a58`，已核验真实旧模板显式升级、重复幂等和未知内容保留。

## 原生部署待验

产品提交推送后，从系统安装器固定产品提交并按 catalog 全路径安装到新 staging；校验后使用同版原生 replace-staged，再显式 upgrade codex-agents。实际完成与清理结果在后续记录中追加，不以离线测试冒充已安装。
