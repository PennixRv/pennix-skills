# W05 实施合同

复用根已批准方案及本任务prd，授权来源为根approval.md。修改集合原生collection.json与sync工作流、对应Skill及参考、必要验收和规范；不新增运行依赖，不复制成员白名单到Lifecycle。Grok固定真实源，Windsurf复用源owner scripts/release/build-package.mjs，完整核对物化树，不留手工overlay。保持manifest的既有archive／npm-pack枚举；npm-pack使用owner正式投影后产物。

文档纠正只改有证据的入口、参数和路径。低影响行文不另造运行时抽象；合成PPTX／中英文扫描PDF从唯一工作目录生成并验证，缺输出不误看cwd旧图，缺语言包在OCR前明确停止。真实依赖由Lifecycle管理，不执行临时安装。

离线集合、根单元、评估fixture、成员原生测试和字节差异通过后，提交推送main；正式交付为固定集合提交和根W08—W11两端原生部署／重装。必要失败停止依赖发布，最终停止点沿根合同。

## 验收覆盖

| 接受条件 | 工作包 | Owner | 验证入口 | 交付证据 | 停止条件 |
| --- | --- | --- | --- | --- | --- |
| 固定源与物化同一内容 | W05 | Grok／集合 | 固定archive全文件／字节、原生test | 无overlay、失败／来源路由一致 | 同步恢复旧规则 |
| 正式消费者包 | W05 | Windsurf／集合 | build-package、消费者manifest和树比对 | 无scripts／devDependencies、allowlist相同 | 源npm pack旁路 |
| 现行入口与任务落点 | W05 | 集合 | collection verify、引用核对、既有评估fixture | 无退役Skill依赖，连接字段正确 | 秘密正文或旧接口复活 |
| 文档示例可执行 | W05 | 文档Skills／依赖owner | 合成PPTX、OCR中英／缺语言正反例 | 当前目录与真实页／语言／超时 | 旧图冒新图、默认英文OCR |
| 固定交付与保留 | W08—W11 | Lifecycle／宿主 | 两端repair及来源核验 | 实际重落盘、无身份数据覆盖 | no-op冒重装或局部冒完成 |
