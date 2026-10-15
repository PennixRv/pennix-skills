# 实施与验收

## 前置条件与源码

- 用户批准 revision 1；CCH 0.1.46 Release、精确归档重装、doctor、运行态版本及 13 个编译模块字节比对均已通过，真实 tmux render 包含计时段。
- 本地 main 仅快进到已核验的 origin/main `1c1c1a4444bfb2f81ca5343dde3b00c21412bafe`；原生 start 成功，未重置其他分支。
- 产品配置仅将 `components.cch-status.approved_version` 从 0.1.45 改为 0.1.46；其他组件、配置目标、AGENTS 模板和集合合同未变。
- 现有测试通过：test_lifecycle.py 81 项、test_managed_collection.py 13 项、test_skills_install.py 31 项，共 125 项；无新增镜像测试。JSON 解析、单字段结构差异和 git diff --check 均通过。
- 既有集合 discover 显示 match，collection_integrity=match，PyYAML ready；具备完整暂存后原生替换条件。

## 部署

- 版本提交 `f202fe495cb52d39cdcfb36647a0a657d3528cb2` 已推送 main；系统 skill-installer 以该精确提交、catalog 全部路径和 git 模式完整暂存 15 个 Skill。
- 暂存成员集合、frontmatter、seed 可执行位及 catalog 与来源一致性检查通过；从暂存生命周期入口执行 replace-staged，原生回执 changed。未直接编辑安装集合或私有收据。
- 全新 discover 的 pennix-skills、collection_integrity 和 cch-status 均为 match；源码与安装 catalog 字节一致，CCH 固定与实装版本均为 0.1.46。
- `verify --component pennix-skills --yes` 与 `verify --component cch-status --yes` 均为 match，failures/advisories 为空。
- profile_status=match，无需 reconcile；未重新配置凭据。无需回退。
- 全量 `verify --yes` 返回 blocked，唯一 failure 为 ponytail-plugin 实装 5.2.0、catalog 固定 5.1.0。升级前 discover 已存在同样漂移，已与本任务成功结果区分，不扩展修改其他组件。
