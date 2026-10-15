# 实施与验收

## 前置条件与源码

- 用户批准 revision 1；CCH 0.1.46 Release、精确归档重装、doctor、运行态版本及 13 个编译模块字节比对均已通过，真实 tmux render 包含计时段。
- 本地 main 仅快进到已核验的 origin/main `1c1c1a4444bfb2f81ca5343dde3b00c21412bafe`；原生 start 成功，未重置其他分支。
- 产品配置仅将 `components.cch-status.approved_version` 从 0.1.45 改为 0.1.46；其他组件、配置目标、AGENTS 模板和集合合同未变。
- 现有测试通过：test_lifecycle.py 81 项、test_managed_collection.py 13 项、test_skills_install.py 31 项，共 125 项；无新增镜像测试。JSON 解析、单字段结构差异和 git diff --check 均须通过后提交。
- 既有集合 discover 显示 match，collection_integrity=match，PyYAML ready；具备完整暂存后原生替换条件。

## 部署

待精确提交完整暂存、原生替换及全新核验后追加结果。不得直接修改安装集合或私有收据。
