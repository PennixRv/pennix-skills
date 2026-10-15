# 实施计划

1. 本任务计划封口并取得后续针对当前版本的明确批准；依赖 CCH 0.1.46 发布重装验收已完成。检查 main/远端/工作树，仅快进本地 main 到已核验基线，再原生 plan approve/start；不切换或停止其他仓库任务。
2. 读取适用指南和 lifecycle/skill-installer 当前合同；精确修改 catalog 的 CCH approved_version。复核其他 JSON 结构和值未变。
3. 运行现有 unittest：`python3 -B -m unittest discover -s skills/pennix-component-lifecycle/tests -p 'test_lifecycle.py'`、同目录的 `test_managed_collection.py` 与 `test_skills_install.py`；运行 JSON 解析及 git diff --check。记录检查结果，不为单字段改动增加实现镜像测试。
4. 提交推送 main；记录精确提交，复查远端 main。只读 discover 后，使用系统 skill-installer 从该提交完整暂存已声明集合，按 design 的新 lifecycle 入口执行原生 replace-staged。
5. 全新 discover、集合完整性核验和 `verify --component cch-status --yes`；需要时按原生安全条件执行 workflow-state 摘要 reconcile。运行全量 verify 并区分本次成功与既存无关失败，不擅自升级其他组件。
6. 在 verification.md 记录源码/安装版本、精确提交、集合核验、profile 是否需要刷新、回退状态及根协调关联；原生完成与归档，回传根仓库验收。

执行前动态核验：版本 tag/Release 是否实际存在且校验正确、集合来源和收据是否仍可验证、远端提交是否变化。不允许伪造路径、SHA、回执或以直接覆盖安装副本绕过冲突。失败按 design 回退并保持包/清单一致，未验证不报完成。
