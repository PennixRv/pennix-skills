# Implementation Plan

## Gate

本 task 独立原生 seal 后与根任务一起展示；必须有后来明确覆盖本组件当前 revision 的实施批准，再原生 plan approve/start。root 批准本身不替代此门。主会话实施和检查；读取 before-dev、当前目标/接口/spec 并保护无关改动。

## Steps

1. 核对 HEAD/branch/工作树/源模板摘要/安装状态，创建 `task/optimize-user-agents-template`，依原生入口启动已批准任务；若动态变化带来实质冲突先 replan。
2. 编辑 design.md 所列模板和既有分层断言；保留 owner Skill 细节。逐段核对原用户需求、五个段落、必要反例、批准门、原生入口、继续恢复和证据保护。
3. 从批准前已固定 Git 基线保存完整旧模板夹具，登记其精确摘要；更新最终 catalog SHA，拓展已有升级测试中的旧版与个人漂移两类场景。不改算法、不允许任意摘要或绕过安全检查。
4. 在本仓库运行以下既有验证，不添加只为文案改写的新测试框架：
   - `python3 -m unittest discover -s skills/pennix-workflow-routing/tests -p 'test_*.py'`
   - `python3 -m unittest discover -s skills/pennix-fastctx-routing/tests -p 'test_*.py'`
   - `python3 -m unittest discover -s skills/pennix-decision-grill/tests -p 'test_*.py'`
   - `python3 -m unittest discover -s skills/pennix-component-lifecycle/tests -p 'test_*.py'`
   - `git diff --check` 与批准文件范围审阅。
5. 提交、合 main、推送，核对真实远端 commit；记录提交与模板 SHA。无需额外 package release，不顺带更改 Extra pin 或其他组件版本。
6. 用受信 system installer 按既有清单下载已推送提交的精确集合路径到 staging，并用新 lifecycle 原生 replace-staged 接纳；先临时目标验证，再本机。原生 discover → `upgrade --component codex-agents --yes` → fresh verify。发布内容与安装目标对应，不从本地源目录复制到安装态。
7. 检查源/目标字节与 catalog 摘要、有效 AGENTS 来源；核验 Pennix/Extra 集合 match，后者源 SHA 与树不变。根任务负责新宿主只读加载和组合验收，共享证据但不把 root 报告当成本组件通过。
8. 固定验收与回滚记录，按当前组件原生 finish/会话记录/Git/归档收敛。执行进度放未封口记录，不改已封口 PRD/design/implement。

## Checks and Failure Boundaries

精确旧版升级成功且相同新版本幂等；旧版添加个人文本必须失败且字节保留；现有原子失败、symbolic-link/owner/权限/override 负例仍通过。源摘要/candidate drift/安装来源不明时停止，不手写 receipt、不覆盖个人改动，不以库文件存在或字符串匹配替代物化验收。

回退遵守 design.md 的纠正提交方案。仅相同 scope/owner 的文案小校对可复用本方案；重要公开行为、来源、部署范围或验收改变必须 replan、封口、展示并取得后续批准。

## Planning Closure

2026-10-12：与根任务用户决策和证据矩阵对齐，修改目标六个组件文件/夹具、组件分支、质量门、Git 分发、本机原生接纳、迁移保护和纠正回退路径已固定；无阻塞性静态选择。task 产物非空且相关链接有效，当前工作树只有本规划任务目录，无受保护目标变更。未运行任何实施或安装操作；动态 HEAD/摘要在批准后重新核对并写未封口执行记录。本文件原生封口后不用于追写进度。
