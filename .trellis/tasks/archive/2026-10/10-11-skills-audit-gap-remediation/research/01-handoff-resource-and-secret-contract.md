# handoff 端到端资源与秘密合同复核

## U2：资源

- 既有用户 D1/D2/D3 已确定核心必读、完整公开历史按需、单一 JSON/prompt、不维护旧语义兼容。本轮不会把重复询问保真或引入旧语义分支作为方案起点。
- `handoff.py:245–382` 逐行读取 rollout，但累积 candidates、timeline、coverage spans、topic/repeat 和工具 ID 集合。`build:446–462` 返回全量对象。
- `workflow_contracts.py:68–79` 对完整文件 `read_text`、`json.loads`，随后 `json.dumps` 扫描秘密。`handoff.py:_core:823–831` 调用该路径，所以 validate、read、lifecycle、ownership 都承受全量历史内存。
- `read_view:735–743` 和 `_view_text:711–732` 先完整生成所选视图，再截取分页；`_validate_history_reading:746–764` 也完整生成视图计算长度。
- `render_handoff_prompt.py:75–98` 经 `_core` 载入历史，却只需要核心和统计。`_archive_snapshot:1201–1215` 又完整载入 JSON 校验；归属 digest:57–66 已经分块，copyfile/归档复制路径不需重新实现。
- 本环境未安装 `ijson`。保持单 JSON 且不自己造增量解析器的候选需要说明成熟流式解析依赖、安装来源与失败条件；另一个候选是 core/history 分离，但会重开既有文件边界并增加绑定、retention/恢复整体性合同。均未选定，也未安装依赖。
- 当前结论：F07 必须以 write、validate、read、render、admit/history range、status/ownership、retention 的端到端资源验收关闭，单改输入循环或输出分页不能关闭。

## U3：秘密

- `workflow_contracts.py:11–17` 的 SECRET_RE 对有限前缀和未加引号字段名匹配。`load_json_file:77` 及 handoff request/event 检查先序列化完整对象，导致 JSON 字段分隔前后的引号阻断部分模式。
- 用 AST 读取正则并使用纯合成值的只读自检：`free_api_key=true`、`json_api_key=false`、`json_password=false`、`free_token=false`、`prefixed_xai=false`、`plain_normal=false`。不读取或输出真实秘密，不创建产品测试或交接包。
- 历史 `_short_text:178–186` 当前命中后替换整条文本为 `[redacted: possible credential]`；request、结构化载入、事件采用拒绝。安全策略应保留这两类输入的区别。
- 检测任意未知秘密无法由通用正则保证。必须明确检测范围与源侧核对责任，禁止把有限检测写成秘密零遗漏的保证；已知遗漏应通过结构化值检查和已知格式覆盖修复。
- 待用户决定的实质行为：历史检测命中后继续以脱敏占位保存完整事件，还是整包拒绝、要求源侧处理后重新生成。两者都拒绝请求摘要、事实与 receipt 中检测到的秘密；都不修改原始 rollout。

## U2 补证：成熟流式解析与文件边界

- 2026-10-11 经 Grok fetch 获取 [ijson 官方仓库 README](https://github.com/ICRAR/ijson)，本次结果未截断。原始检索结果留在本机临时目录，不提交 Git。
- 官方说明 `parse`/`basic_parse` 可以处理解析事件，避免构建完整对象；默认 `buf_size=65536`，有 `python` 后端和主流平台二进制 wheel。解析返回的字符串值仍完整存在，不能用读取缓冲大小推导任意输入的内存上界。
- 默认非整数是 Decimal；后端的非法数字/不完整 token 能力有差异。若采用依赖路线，必须选择并验证适用后端、当前 schema 数值语义、严格结构与重复键处理，不能因流式处理弱化验证。
- Pennix 当前 handoff 未声明独立解析依赖；collection installer 的现有格式就绪检查只有 PyYAML。新增 ijson 会涉及 handoff 运行就绪、安装前置合同、CI 和失败提示，不能只在开发机装包后宣称交付。
- 标准库候选是分开小型 core JSON 与逐记录历史 JSONL；不自造流式 JSON parser。代价是重开既有单 JSON 决策，并把附属历史的摘要、大小、引用和 lifecycle/retention 原子性纳入合同。所有增长索引仍需临时磁盘，单独拆文件不等于端到端有界。
- 两种方案都保留完整历史；资源验收采用固定记录大小的多级规模及进程限制，另测超长记录与磁盘/输入失败。不能承诺绝对常量内存，也不能以截断历史完成验收。

## 当前返回动作

D2 已选择“脱敏后继续”，保留非秘密历史上下文。D3 已选择 core 与历史分离，标准库实现，不引入 ijson；下一步在 design/implement 固定整包绑定与端到端验收。小样本只证明逻辑缺口；无 OOM、实际秘密泄露或大输入资源基准结论。
