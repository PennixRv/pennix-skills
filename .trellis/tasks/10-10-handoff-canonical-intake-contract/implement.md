# 组件实施与交付计划

## 前置门禁

1. 完成并核验 PRD/design/implement，原生 plan seal；展示组件与根当前版本，等待随后明确实施批准。设计选项答复不作批准。
2. 批准后分别原生 plan approve/start，加载 trellis-before-dev 的适用规范；主会话 inline 实现和检查，不派发节点。重核 main、origin、已有差异和安装状态，保留无关工作。

## 有序实施

3. 在现有两份测试中先加入真实缺口回归：conversation 错误类型/缺项、候选/引用/覆盖矛盾受控失败，不测试仅匹配实现文本。
4. 新写 schema 10：复用已有 rollout_identity，只保留一个 conversation；timeline 引用 event_index，不复制正文。同步共享校验，保留完整投影与所有合法例外。
5. 实现只读 read 核心/历史视图和无损分页，复用规范校验与文件读入口；明确续读位置、结束与输入错误，不写游标台账。
6. 更新新 attestation、必读步骤及 admit 阅读范围，维持源门禁、身份、顺序、幂等和初次停止。旧包沿只读门禁，不实现旧语义写分支。
7. 同步渲染器、Skill 请求/读取/声明示例和全部 fixture；核对所有实际消费位置。渲染器复用版本和校验入口，历史 prompt 不重写。
8. 人工检查差异和跨层数据流；仅将已实现可复用合同记录到组件 backend 质量规格，不为本任务全面填充占位 spec。

## 验证

- 主回归：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py'`。涉及原生交接协议的测试通过原生 exec 入口运行；所有新逻辑均有行为覆盖。
- 新格式：唯一候选/覆盖位置、timeline 引用、全部合规文本/来源/排除数据保持；空记录、未知记录、NUL padding、尾部 partial 和不完整工具调用作为合法覆盖情形。
- 校验：错误映射/列表/字段/类型、布尔伪装整数、索引重复/越界、错误 supersedes/来源边界/计数，均在 validate/read/render/lifecycle 入口受控失败。
- 阅读：大历史、超长单条、多字节文本、长核心摘要，无损逐页拼接和明确结束；中断、非法页参数、未读/部分/完整历史声明、旧 core_read 拒绝。
- 生命周期：源 pending、不正确/源复用身份、缺失或乱序必读步骤、相同目标重试、不同目标拒绝、archive/restore/reopen/purge 的配对一致性和幂等。只在隔离 fixtures 运行写操作，不接纳原样本。
- 历史边界：schema 8/9 配对文件与不透明旧收据字节保持，所有写入口拒绝；不测试或实现旧阅读语义继续。
- 集合质量：按现有 CI 枚举所有 Python Skill 测试模块执行一次；用既有 validate_staged_collection 检查 catalog 成员、frontmatter、PyYAML 和执行权限。仅校对本轮中文文档并人工核对语义，不新增风格 CI。
- 原生 task validate 与 git diff --check；根执行既有 `node scripts/run-workflow-integration.mjs --offline --pretty`。不全量运行未修改的 Trellis/CCH/Grok 网络流程。

首次失败先保存完整错误、重读相关文件再修改；检查已通过后只因新变化或未解决问题重跑。

## 提交、发布、安装与收敛

9. 完成源码和测试检查后，组件 main 提交推送产品及任务证据，核对 origin/main 精确提交。当前交付机制是 GitHub main 的精确提交，不新增 npm 包、标签或 Release。
10. 根按当前 seal 中的 implement 使用系统 skill-installer：固定产品提交、读取唯一 catalog 的全 12 路径、git 模式安装到新建同级 staging；先验证来源、成员、内容和可执行模式。
11. 从已验证 staging 的 lifecycle 原生 replace-staged 更新 `/home/penn/.codex/skills/pennix-skills`；安装入口原生 scoped verify，逐文件与产品提交比较内容和执行权限，确认命令链接及 staging 已消费。
12. 保存组件 verification/deployment 与根 acceptance 的真实结果、产品/最终提交和限制。源及消费者间只传交付资产，不复制私有回执、日志、转录或凭据。
13. 分别用原生 task archive（非 PR main 使用明确 skip-branch-validation 例外）和 add_session 收敛组件与根；推送组件归档/日志提交。归档后产品树未变则不重复安装，根无 remote 只本地提交。

## 回滚与再规划

安装旧产品基线为 d7bb1852a81bfd595631b96f39918fcb7468dd89。事务失败依原生回滚保留旧安装；若新行为经交付后确认回归，仅 revert 本轮产品并从安全基线重新原生 staging 替换，不回退任务证据或历史包。

新增依赖、维护仓库/接口/风险/验收范围变化时原生 replan 并等待新版本批准；正常同范围低风险修正直接推进。未知安装漂移、远端并发差异或检查失败先诊断，不强推、不覆盖、不手改原生运行态。
