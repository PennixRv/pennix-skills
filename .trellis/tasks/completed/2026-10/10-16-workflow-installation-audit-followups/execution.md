# 实施记录

## 授权与修改边界

用户阅读根侧完整四项方案后明确答复“批准”。根侧和本任务均已原生 seal revision 1、approve、start，当前为 in_progress；进度只写本记录，不修改已封口材料。

修改目标为本仓库 main：catalog 纳入 pnpm 并对齐两个已核验版本；`scripts/adapters/skills_install.py` 负责精确暂存快照与丢弃；`scripts/lifecycle.py` 负责公开参数和结果；新增实际文件系统行为测试并沿用 npm 迁移回归；lifecycle Skill、resource-cleanup Skill 与资源策略说明新入口。安装副本只由系统 installer 与原生 replace 更新。

差异验收覆盖调用入口、默认只读、完整摘要、路径／owner／链接拒绝、目录替换和删除失败，以及原有集合／收据／命令不变。保留 Trellis 的 pnpm pin 和 beta 分支、Paseo daemon、既有配置选择及其他资源。

## 结果

- lifecycle 完整回归：`python3 -m unittest discover -s skills/pennix-component-lifecycle/tests`，200 项通过；其中暂存丢弃新增 12 项。最初 CLI 夹具错误影响了 catalog 的同名校验函数，已改用真实清单成员，完整回归随后通过。
- 两个受影响 Skill 的 system quick_validate 均通过；中文检查 error=0、warning=0，6 条引号样式建议涉及既有正文，按本集合保留中文弯引号的约定不改写。
- 主会话按 trellis-check 复核 CLI → adapter → 原生删除及 catalog → 既有 npm 迁移的调用链，确认默认预览不调用全局 discover、不创建收据；活动集合完整性摘要合同不变。核验与删除的非事务限制已保留在源码及说明。
- `git diff --check` 通过；没有新增依赖或未解决的实施范围问题。准备提交推送源码，再安装该精确提交并进行实机验收。

## 安装与实机结果

- 源码 bf589b9 已推送；系统 skill-installer 以精确 SHA／git 模式暂存 16 个 Skill，frontmatter 与 seed 执行位通过，从新暂存原生 replace 成功，集合 scoped verify 为 match。
- pnpm 原生 upgrade 成功：10.32.1 安装到 `/home/penn/.local`，包和 pnpm／pnpx 由 penn 持有，`/usr` 原包及两个入口已移除；默认 prefix 保持用户目录。TTY 中的 zsh 回读无错误、两个入口均为用户目录。非 TTY 的首次交互 zsh 探测出现 monitor／gitstatus 初始化提示，改由宿主 TTY 正常核验，未改 Shell 配置。
- Trellis 的 `CI=true pnpm install --frozen-lockfile --offline --ignore-scripts` 成功，锁文件及工作树无变化。额外 compiler 探测起初在无该直接依赖的根包调用失败，核对 package.json 后改用两个真实子包的 `pnpm --filter ... exec tsc --version`，均为 5.9.3；未修改产品或工具链 pin。
- Ponytail 原生 Marketplace remove／add --ref 成功，HEAD 精确为 6f1c2bfff0c837d268929a7c4e490918eb4fab29，插件仍 installed/enabled 5.3.1，无需补装；已安装的 27 个相关资产与发布提交一致。
- 精确 stage 原生 preview 为 8 条目、23,901 文件字节；以同一摘要执行回执 executed，目标不存在，活动集合摘要、收据 SHA-256 与命令链接前后相等。此数不表示物理块释放量。
- pnpm、Ponytail、AoE、pennix-skills 四个 scoped verify 全部 match，无 failures／advisories；AoE 原有 upstream hash 仍 match。根侧离线集成 8 passed。

## CI 修正

源码提交的 GitHub CI run 38913098678 报告三个已有 npm 测试失败：重复包夹具将当前临时目录 owner 错比 HOME=/tmp 的 root owner；漂移夹具把 root 当作必定不同的 owner；真实 npm prefix 测试在未安装 npm 的容器中运行。新增暂存 12 项在远端已通过。

这些失败位于本次复用的 npm 迁移验证链，按同组件、低风险测试修正继续：owner 从实际临时目录取值，漂移期望明确隔离，CI 测试容器补齐已有真实配置测试需要的 npm。未改生产所有权逻辑、删除边界或封口范围。本地完整 200 项再次通过；与 CI 同样使用 HOME=/tmp 的 test_lifecycle.py 90 项通过。待修订 CI 通过后再归档。

完整原生 `verify --yes` 已为 match：17 个组件、核心／已启用配置核验通过，failures=[]、advisories=[]，staging 为 none。无需刷新 profile 摘要或变更任何配置选择。

## 最终验收

修订 `34870dde8c51fe205bb1ec34f4e5f7a7eda19993` 的 [GitHub CI run 38913898442](https://github.com/PennixRv/pennix-skills/actions/runs/38913898442) 为 success，Python Skill 测试及 native evaluation driver offline 步骤均成功。系统 skill-installer 以此精确 SHA 重新暂存完整 16 Skill，frontmatter／seed 执行位通过，原生 replace 成功；8 个本轮受影响安装文件与来源逐字节相同。

最终重装后的完整 verify 仍为 match，17 个组件、核心／已启用配置通过，failures=[]、advisories=[]，staging=none；根侧重新运行离线集成，8 passed、其余计数全为 0。

PRD 的 C1—C5 和四项验收均已有真实证据，达到源码推送、集合安装、pnpm 迁移、原生插件来源对齐、AoE 核验、精确 stage 清理和组合验收的完成点。后续仅提交本记录、原生归档和日志；这类任务／工作区记录不改变已安装的 Skill 内容树，无需再装同一内容。

保留限制：Ponytail 上游插件 manifest 仍为 main；已核验 Marketplace 固定提交及实装发布资产，未宣称插件下载提交天然不可变。stage 核验和删除非事务、已丢弃内容不可自动恢复，23,901 字节不表示物理块变化。未执行新主机 seed bootstrap、付费节点或无关服务／项目升级；这些不属于本轮验收。
