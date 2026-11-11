# 执行记录

## 2026-10-16

- 已完成原计划的 catalog、host、发现/核验与迁移顺序修改，提交 `9e8ada1c402bb2f578309861cb08a6d0c8d1012d`、`1d29b5b`、`5af71d66a85e2812265ee37513825c0950fa14c9` 均已推送 `main`。最后一次 lifecycle 专属 unittest 为 182 项通过；同时已运行编译与差异检查。
- `1d29b5b` 修复迁移前置检查错误查询系统 root；`5af71d6` 修复 subprocess argv 中逻辑 `$HOME/.local` 未展开的问题，并调整回归用例覆盖安装命令的展开结果。
- 根任务已通过原生暂存接纳安装集合，并迁移 Trellis、FastCtx、CodeGraph、CCH、Paseo；实际安装/运行态证据由根任务保存，本仓库不复制用户配置、日志或会话。
- 实施期间曾把清单进度写回已封口 `implement.md`；已按记录中的摘要恢复其完整原始字节，后续进度只写本未封口文件。

## decision-needed

- 用户要求评估并倾向把 npm 用户默认 prefix 纳入 lifecycle 正式管理。这会增加配置职责及公开动作，须原生 replan 后收敛方案并重新封口批准。
- 建议复用现有 catalog 与配置/核验机制，增加显式用户配置入口，仅管理 npm 用户配置的 `prefix`。各 npm 包继续使用已固定的显式安装 prefix；不顺带修改系统或项目配置，不读取/输出其他 npm 配置值。
- 根任务停止新增配置实现；现有迁移结果和 182 项测试仅证明 revision 1 行为，不能代替新配置行为验收。

## 用户已收敛修订

- 用户明确要求将 npm 用户默认 prefix 逻辑直接注入现有 lifecycle 安装/升级流程，由 Skill 说明，不新增组件或配置入口；此前显式 configure 建议已淘汰，不再 grill。
- 最小修订计划见 revision 2 的 PRD/design/implement；目标值仍为既有 catalog 的 `$HOME/.local`。尚未修改 revision 2 产品源码、测试或安装副本。

## Revision 2 实施与源侧验收

- 用户在两个任务 revision 2 封口展示后回复“批准”；两侧均已通过原生 plan approve/start 恢复 `in_progress`。
- `lifecycle.py` 新增小型 `ensure_npm_user_prefix`，在既有用户级 npm 安装/升级路径执行原生用户级 npm 配置及回读；已匹配包也覆盖，默认值已匹配不写入。非用户级 npm 返回无变更，卸载及只读流程不进入该设置路径。配置失败停止后续安装与旧包清理，已成功设置的默认值不因随后安装失败而恢复。
- `SKILL.md` 的 npm 合同段落已明确这一副作用与边界；没有新增组件、子命令、catalog/profile 字段或收据。CodeGraph 迁移测试只隔离新增的配置步骤，继续单独验证包迁移顺序；新增 lifecycle 测试覆盖整体配置/安装/清理顺序和失败边界。
- 完整 lifecycle unittest：188 项通过。随后将原生 npm 测试的 cache 也放入临时目录，并重新运行 `test_lifecycle.py` 全部用例通过；测试只改临时 npm 配置与缓存，验证原生 npm 保留无关 registry/fund 键及重复执行不改文件时间。
- `py_compile` 与 `git diff --check` 通过。中文 Skill 检查 error=0、warning=0；两项既有中文引号样式建议按当前写作 Skill 的常用中文引号约定保留。
- 本轮主会话已按 trellis-check 复核受影响入口、包匹配时的配置路径、前置检查顺序、错误传播及旧包延后清理；未扩展到其他组件源码。真实活动集合和用户 prefix 验收由根任务继续执行，完成后再归档组件任务。

## 真实交付接纳

- 最终产品提交 `949760ea56ab2bdebccf48aa7b17e0b0ce0d6a45` 已推送 `origin/main`。根任务通过 system skill-installer 从该精确提交暂存，并用暂存树原生 `replace-staged` 接纳成功；活动脚本和 Skill 与源字节一致。
- 活动集合 `verify --component pennix-skills --yes` 为 `match`，failures 为空；旧未知暂存目录仅有 advisory，未接管。真实 `upgrade --component trellis-cli --yes` 返回 `no-op`，当前用户默认 npm prefix 为 `/home/penn/.local`。
- 根任务确认五个目标用户级包和入口 owner 均为 `penn`、旧 prefix 无目标副本；Paseo 客户端已恢复，CCH doctor 和双侧真实 render 通过。组件任务的 catalog/行为/测试/发布/安装接纳验收已完成。
- 完整基线仅剩原有 Ponytail/AoE 固定版本漂移，根任务已记录后续；未登记的系统级 pnpm 也由根侧后续审计任务承接，不在本组件任务自动扩展治理范围。
