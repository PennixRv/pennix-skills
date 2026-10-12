# 第二 Skill 集合实施

## 来源与目标

根完整 revision 3 已批准；P0 中间版本已通过分发和宿主落点。精选 fork PR #1 已合并，公开 main 为 `PennixRv/pennix-skills-extra@c205b3960602902536ba48bbad5b028803fbf7ab`，十项源码目录沿上游原位保留。独立集合 ID/目录为 `pennix-skills-extra`，唯一可执行清单与固定 SHA 写入 lifecycle catalog。

## 当前单元

先读取并定位 catalog 校验、collection resolver、各调用方、动作 owner 分派及树/receipt 事务，然后实现 managed install/upgrade/verify/uninstall。保留旧 Pennix native-owner、bootstrap、命令物化与 schema 2 receipt 合同。新集合不配置 MCP/Hook/凭据，也无安装后命令。

新集合只接受受信宿主 system installer helper 和 catalog 固定 argv，不执行 target CODEX_HOME 内脚本。receipt 核验区分完整旧 SHA 可升级、相同 SHA 幂等与来源/活动漂移拒绝；部分下载、校验、切换或 receipt 写入失败保留旧树及另一集合。行为验证按组件 implement.md 矩阵进行，未完成前不部署设备。

## 接口核对

实际事务模块为 `scripts/adapters/skills_install.py`，不是 scripts 根目录；错误路径的单文件读取已据实际错误纠正，没有误报工具缺失。已完整读取目标解析、frontmatter/树安全、摘要、schema 1/2 receipt、暂存校验、替换/命令/思源回滚及卸载事务。

`lifecycle.py` 的校验、probe/discover/verify、配置父集合、旧状态协调、暂存发现、managed 分派和 replace-staged 均有旧集合硬编码或未传入 target codex_home 的解析调用；调用方已搜索定位。新集合走 delivery collection 的共同接口，仍保留旧 bootstrap/物化/命令以及 replace-staged 只接纳旧集合的合同。

宿主 system helper 为实际声明的 `$CODEX_HOME/skills/.system/skill-installer/scripts/install-skill-from-github.py`，导入同目录 `github_utils.py`。本机该路径与祖先均无 symlink、由当前用户或 root 持有且无组/其他写权限；部署实现据此检查受信宿主位置，不从 `--codex-home` 目标寻找或执行 helper。

准备在现有事务接口增加新集合专用来源 identity（repo、40 位 ref、精确 names）与 schema 3 receipt；旧 schema 2 不迁移。新集合允许完整同源旧 SHA 升级/退回、同 SHA 无操作，缺失/漂移/未知来源或孤立 receipt 阻断。下载仅使用 catalog argv、同父随机暂存、download 模式；支持引用、逐目录来源/许可和 Skill 协作引用须在接纳前闭合。所有新非平凡逻辑配结果导向的行为测试，源码未修改时不宣称这些机制已实现。

## 首轮实现与验证

已在上述实际源文件实现共享目标解析与调用方、新集合专用 schema 3 identity/receipt、受信宿主 helper 及其 `github_utils.py`、固定 argv 下载、支持引用/来源/许可接纳、managed 操作与来源状态。旧集合保留 bootstrap、物化、命令、schema 2 和 native-owner install/upgrade；replace-staged 仍只允许旧集合。catalog 已固定公开精选 SHA `c205b3960602902536ba48bbad5b028803fbf7ab`，没有新增来源或任意执行器参数。

完整 lifecycle 全量 176 项通过，覆盖原生入口分派、同 SHA 无操作、完整旧 SHA 升级/退回、部分下载、缺失/越界支持和未登记 Skill、receipt 写入/树切换/receipt 切换失败恢复、宿主 helper 信任、私有来源与漂移拒绝、分别卸载时另一集合的字节/模式/所有者/receipt 不变。`python3 -m py_compile` 和 `git diff --check` 均通过。

真实固定 SHA 已在隔离临时目标执行 native install/verify/upgrade/uninstall：install 返回 `changed`，verify 的 `pennix-skills-extra` 为 `match` 且 `failures=[]`，同源同 SHA upgrade 返回 `no-op`，uninstall 返回 `changed`，卸载后目标只保留空的 `skills/` 父目录。此次现场使用实际 Arch WSL2 宿主和实际 system installer helper，但未写入正式 `CODEX_HOME`。组件源仍待提交、推送，并待 Trellis 发布和正式生命周期落点。
