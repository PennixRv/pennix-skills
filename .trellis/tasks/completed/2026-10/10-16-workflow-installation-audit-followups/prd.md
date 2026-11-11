# 统一收敛安装审计遗留与精确暂存清理

## 目标（Goal）

承接根任务已明确要求统一收敛的安装遗留：通过本组件的唯一 catalog、既有原生部署路径和最小暂存丢弃入口，使 pnpm、Ponytail、AoE 和本次 stage 的实际状态可验证一致。当前保持 planning，完整展示和批准后才实施。

## 需求（Requirements）

- C1：catalog 新增 pnpm 10.32.1，用户 npm prefix 为 `$HOME/.local`、owner 为当前用户，公开候选 tag 固定精确版本。复用已有 npm 迁移／重复包核验，不新增迁移器；pnpm 与 pnpx 均纳入真实验收。保留 Trellis 的 packageManager 和锁文件。
- C2：Ponytail approved_version 对齐 5.3.1，Marketplace ref 固定已核验的发布提交 `6f1c2bfff0c837d268929a7c4e490918eb4fab29`；Codex 原生接口负责切换快照，保持插件启用并核对实装与发布资产。上游插件 manifest 仍引用 main，不改写第三方来源或声称插件安装提交已固定。AoE approved_version 对齐实装／候选 1.20.0，保留 AUR owner 与现有 installer hash。
- C3：新增 lifecycle `discard-staged` 原生入口，仅面向显式指定的 pennix-skills 暂存，默认 dry-run；实际删除需 `--yes` 及匹配的预览摘要。路径必须处于选定 Codex home 的 skills 下、名称为本集合的暂存、当前用户持有、无符号链接，且树为有效集合或成员子集；异常、越界、非集合顶层条目或已检测变化均闭锁。复用已有安全路径和 frontmatter 校验；删除摘要覆盖全部待删对象，不使用忽略缓存的活动集合摘要。核验与删除不承诺事务保证，不创建自动 GC、TTL、来源收据或第二套状态。
- C4：同步 lifecycle Skill 对显式丢弃与自动发现的区别，以及 resource-cleanup 的安装集合入口索引。discover 仍只报告未知 stage，不自动读内容、清理、推断来源／年龄／活动状态或接纳为已安装集合；其他资源不受影响。
- C5：源码与测试只在本仓库 main 修改，根侧只协调。检查后提交推送，从精确提交经系统 skill-installer 新暂存与原生 replace 更新完整集合；不直接编辑用户安装副本。随后迁移 pnpm、原生切换 Ponytail Marketplace、验证 AoE，预览并丢弃本次精确 stage，再执行完整基线及归档。

## 验收标准（Acceptance Criteria）

- [ ] C1 的 catalog 与现有 npm 迁移合同通过检查；本机 pnpm／pnpx 有效入口、owner、版本和项目实际调用正确，旧 `/usr` 包清除。
- [ ] C2 的插件版本／启用、Marketplace 提交、来源／资产及 AoE 包／上游合同通过核验，两个 scoped verify 为 match。
- [ ] C3 的真实预览无写入，执行仅删除匹配摘要的目标；越界、链接、异常 owner、非集合顶层条目、摘要失配或已检测变化均拒绝；摘要覆盖 Python 缓存和根目录身份变化，删除失败如实报告剩余现场；活动集合、收据和命令不变。本次真实清理目标不存在，并记录实际文件字节而非声称物理块回收。
- [ ] 受影响回归、Skill 校验、完整集合安装 verify、完整 lifecycle verify 与根侧集成通过；源码提交、安装来源及限制已记录，组件任务原生归档。

## 备注（Notes）

- 根协调及当前证据：`/home/penn/devel/codex-workflow-optimization/.trellis/tasks/10-16-workflow-installation-audit-followups/`。
- 精确清理目标为 `/home/penn/.codex/skills/.pennix-skills-stage`；当前只有 pennix-workflow-routing 子目录，8 个条目、普通文件 23,901 字节，未发现异常对象。创建来源仍未知；其 frontmatter 名称与目录一致，不能据此证明来源或闲置。
- 不新增 npm 依赖，不修改 Trellis／Paseo／NAS，不升级 pnpm 大版本，不扩展其他 stage、缓存或历史清理。用户本轮收敛请求尚不是对本次完整方案的最终实施批准。
