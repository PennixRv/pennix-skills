# U7：Windsurf 受管命令与升级合同

## 用户要求与证据

- 根 D7 同次补充要求 Windsurf 像 Grok 一样通过 PATH 调用；这是明确的本轮新增需求，无需重复询问。
- catalog 的 commands 与 `skills_install.MANAGED_COMMANDS` 当前只声明 Grok。已有 replace_collection 验证执行位、目标路径、私有树收据、链接归属、PATH 遮蔽，再事务性替换树、收据并创建链接；失败删除本次新链接并恢复旧树/收据。
- Windsurf 上游 package bin 已是 `bin/windsurf-code-search`，无需新包装器或全局 npm 安装。
- `collection_receipt_state:214–215` 只接受空 map 或完整当前 map；`replace_collection:330–331` 又要求旧 receipt.commands 与新命令全集相等。直接扩大常量会误判有效旧集合，并阻塞既有 Grok 链接复用。
- `test_skills_install.py` 已有私有收据、同名路径、链接失败、原子回退和无收据同目标链接拒绝测试；应扩展实际两命令升级场景，不镜像新实现编造纯文本断言。

## 选定方案

- catalog 追加 Windsurf 的有限映射：target `windsurf-code-search/bin/windsurf-code-search`，link `.local/bin/windsurf-code-search`。脚本验证有限精确映射，不允许用户传任意链接目标；常规 Skill 示例改为命令名。
- 校验“当前实际交付”与“新期望映射”分开。有效私有旧收据、树 digest 和它声明的每个命令均需核验；复用旧链接只凭旧收据逐项证明，不凭新全集相等，更不接管未受管链接。
- 缺失的新链接在事务内增加，成功写新集合完整收据；异常恢复原集合、原收据、原 Grok 链接，只清除本次新建项。发现/核验如实区分完整性与新命令缺失，不将新能力缺失伪装成文件漂移。
- 卸载仍只删除真实收据所有的精确链接；未知路径、不安全目录、执行位问题、另一个 CODEX_HOME 或 PATH 遮蔽全部阻塞。
- `~/.local/bin` 已在 PATH 才能声明命令生效；缺失时保留原生前置条件，不修改 Shell 启动文件。Windsurf configure/readiness 继续从收据集合解析 owner 命令，不转而信任任意同名 PATH。
- 验收：干净安装、有效 Grok-only 活动集合升级到两命令、幂等替换、同名文件/错链接/无证明同目标链接/遮蔽拒绝、第二链接失败回退、两个 CODEX_HOME 争用和精确卸载。活动机 `command -v`、链接实际目标、无网络 `--help` 与 receipt/verify 一并检查。

## 返回动作

证据足以写设计与验收，无需新增 installer 或重复问偏好。当前只写任务资产，没有改 catalog、adapter、用户 PATH 或安装树。
