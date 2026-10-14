# 项目 AGENTS 治理与 CodeGraph 集成

实施根任务 `10-14-project-agents-governance-plan` revision 1 已批准的 pennix-skills 子范围，工作分支 `codex/project-agents-governance`。

- 交付 `pennix-project-agents-governance` 和 `pennix-codegraph-integration`；明确文件内部的手工正文、原生生成块及各自 owner。
- 治理默认只读，按相关改动触发；硬冲突和不安全写入阻断，普通重复与条件张力报告。生成块委托 owner，不隐式初始化/索引/安装。
- 完整 Codex 指令链只读检查覆盖用户、root→cwd、override、fallback 和字节上限；报告候选与限制，不泄露正文。
- routing 只保留分派；lifecycle 源模板只增加已批准一行 CodeGraph 导航，catalog/集合声明同步。
- CodeGraph 从明确旧 AUR owner/版本受控迁移至已发布 Pennix npm 双包；保留配置与索引，未知或失败停止。
- 合同/行为测试、中文检查、原生 staging/集合物化、模板完整性和系统 owner/版本验收通过后收敛。

不编辑安装副本，不接管组件协议，不迁移 Trellis 主仓库、docs-site 或 GitNexus。
