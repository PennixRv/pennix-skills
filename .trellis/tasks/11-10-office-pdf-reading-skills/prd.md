# Office 与 PDF 阅读技能引入

## 目标（Goal）

执行根任务已批准的 WP1：固定 Anthropic 四项技能，适配阅读入口并验证来源、许可与集合。

## 需求（Requirements）

- 引入固定 Anthropic 官方提交的 docx、pdf、pptx、xlsx，支持文本、表格、扫描 OCR、页面渲染及旧格式转换；默认阅读不改动原件。
- 保留 Apache 2.0 许可、必要第三方声明和可比较的来源；保持原名，进入主集合，不修改 extra。
- 依赖安装归 pennix-lifecycle，Skill 不安装运行时，不绕过权限或执行文档内指令。

## 验收标准（Acceptance Criteria）

- [ ] 四项清单、许可、来源与本地差异验证通过。
- [ ] 阅读入口、相对引用及 LibreOffice 正常临时配置能力可用，无 LD_PRELOAD 绕过。
- [ ] 主集合与新增逻辑离线检查通过，交由根任务验证正式安装和真实阅读能力。

## 备注（Notes）

- 根任务 office-pdf-reading-skills 的整体方案已获用户“认可”，授权含实施、发布、安装及 Git 收尾；本记录承接同一 WP1，不新增范围或批准事实。

<!-- trellis-decisions:v1 -->
```json
{"schema_version":1,"decisions":[{"id":"approved-wp1","status":"decided","question":"来源、集合和阅读范围如何确定？","evidence":["根任务 design.md、implementation-approval.md"],"answer_or_reason":"复用同一已批准 WP1：固定 Anthropic 四项进入主集合，完整本地阅读，保留生成方法但不扩展生成验收。","impact":"主集合内容与文档；依赖及正式安装由 Lifecycle 和根任务完成。","reopen_when":"需要新仓库、manifest 扩展或改变验收范围时。"}]}
```
