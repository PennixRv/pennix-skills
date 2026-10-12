# Design

## Ownership and Files

唯一模板权威为 `skills/pennix-component-lifecycle/templates/AGENTS.md.install`。本 task 修改以下文件，根任务承载关联审查和集成测试，不复制模板源码。

| 文件 | 最小修改 |
| --- | --- |
| `skills/pennix-component-lifecycle/templates/AGENTS.md.install` | 第 34 行压缩；决策段加入及时自然留痕原则；第 38 行的系统部署/项目范围拆为清楚的入口规则。 |
| `skills/pennix-workflow-routing/tests/test_contract.py` | 第 58–63 行全局模板断言改为抽象原则/必要反例/原生提问，完整分类仍由 owner 测试验证。 |
| `skills/pennix-component-lifecycle/references/component-versions.json` | 仅更新 `codex-agents.template.revision` 为最终模板实际 SHA。 |
| `skills/pennix-component-lifecycle/scripts/adapters/codex_static.py` | 将当前完整发布模板 SHA 加入既有 `LEGACY_AGENTS_DIGESTS`，不改变识别和漂移保护算法。 |
| `skills/pennix-component-lifecycle/tests/test_lifecycle.py` | 复用现有精确模板迁移测试，加入本次旧版和漂移负例；现有原子失败/override/权限测试继续。 |
| `skills/pennix-component-lifecycle/tests/fixtures/AGENTS.f89b833.md` | 固定本次升级前的已发布完整模板，由该 Git 基线取得，不生成猜造旧版本。 |

## Proposed Text

以下是待实施的精确文案；原有五段结构和其他已审查稳定原则保留。允许不改变语义的小范围中文校对，重要变化回规划。

工具可用性句拟改为：

> 工具可用性以当前宿主实际声明和真实调用结果为准；`functions.exec` 的 `ALL_TOOLS` 仅描述嵌套调用面，缺项不能证明宿主直接工具不存在。调用失败不等于工具缺失；保留原始回执，后续动作遵守负责组件的合同。

决策段新增：

> 围绕明确的小目标推进，及时将关键结论、决策和进度写回已有自然落点，尽量在当前上下文窗口完成留痕，不另建重复台账。

职责段原系统部署/项目执行合并句拟分为：

> 系统部署用 $pennix-component-lifecycle，各安装集合按组件清单声明的动作归属执行；项目初始化需明确授权和项目根目录，不随系统部署自动执行。

> 项目执行遵守当前项目及目标目录适用的更具体规则与已选工作流；Skill 方法不覆盖这些项目约定。

局部规则在宿主指令层级允许的范围生效，不意味着仓库文件可以覆盖 system/developer 或当前明确用户指令。该宿主事实在设计/验收解释，不再把优先级手册塞进模板。

## Existing Owners and Limits

workflow routing、FastCtx、Grill 已有分类与实际调用面合同，无需另造文档来接收删除的枚举。Trellis Brainstorm/research-record 与 Grill 已有证据留痕；新增全局句不重实现它们。中文写作由既有 Skill 承接。Extra 十项已有相关方法与最小交接，不因模板更短而再复制全局合同或修改上游算法。

文本测试约束关键语义，不能保证代理永不误判；宿主生效验收与模板字节/摘要核验分别进行。不新增长度测试硬门槛、工具探测器或无授权 fallback。

## Migration, Delivery and Rollback

当前完整模板摘要 `c73dd09cb6fd26f2b31b286673a73251eb5a900625bb1e1b07f1ceb51a848326` 进入旧版 allow list；最终新正文生成新的 catalog SHA。静态升级只有精确已知完整文件可替换，个人变动/未知内容、模式/owner/symlink 和 override 沿原生保护。集合下载安装仍归 system installer，lifecycle 只做既有 staging 接纳和 codex-agents 原生物化。

隔离通过后本机升级，无远端设备、npm/插件/Trellis 发布。若必须回退，未切换失败保留旧文件；已升级后发纠正 Git 提交，恢复旧正文并把被替换新正文的完整 SHA 登记到原生识别集合，更新 catalog，再升级。旧 adapter 本身不认识新摘要，不能直接退回旧 adapter 后覆写安装态。
