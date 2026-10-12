# 实施与验收记录

## 入口与修改

2026-10-12：用户后续明确批准完整封口包；本任务原生 plan approve revision 1、start，实际分支设置为 `task/optimize-user-agents-template`。批准前基线 `f89b833a490886aa4ecc4e27223ac52ed86105bf` 与动态 HEAD 一致；开始时只有本规划目录未跟踪。

已按 design.md 修改模板三处语义、workflow routing 的全局断言、catalog revision、精确旧摘要集合、既有迁移测试及固定旧夹具。完整分类继续由 owner Skill 承接；无算法、白名单、Extra 或专项方法改动。

## 质量门

- routing 8、FastCtx 5、Grill 9、lifecycle 176 项 unittest 全部通过，总计 198 项。
- 固定旧夹具逐字节等于 `f89b833` 的完整模板，摘要 `c73dd09cb6fd26f2b31b286673a73251eb5a900625bb1e1b07f1ceb51a848326`。真实 adapter 的精确迁移和个人改动拒绝/字节保留通过，原子失败、symlink/权限/owner/override 保护继续通过。
- 新模板 4,585 字节，摘要 `819d4dca89d346d3e8bfb5b8fe26702dee5ddc10ed69cc62293f0b97a5d6a281`，catalog 已同步。
- `git diff --check` 通过；修改符合既有 published user-rule revisions 规范。无需新增规范或测试框架。

## 收敛状态

实施、推送、本机安装、规则物化和验收已全部完成，剩余本记录提交、原生归档与会话记录。

## 发布与安装进度

实施提交 `4624ea6229f09516c626a0bb0c8ced2a759f3a84` 已 fast-forward 合入 main 并推送，远端 main 已核对一致。system skill-installer 依据 catalog 十二项路径，以该精确提交和 `--method git` 分别下载隔离和本机 staging；未从源码 checkout 复制安装态。

隔离过程用 bwrap 将临时目录挂载为进程 HOME，真实 HOME 只读/遮蔽，命令链接和状态写入留在临时目录；未修改宿主 HOME/CODEX_HOME、未复制秘密。native replace-staged 成功且旧 AGENTS 保持；native codex-agents upgrade 成功，新源字节一致；再次升级 no-op。codex-agents 与 Pennix 集合 scoped fresh verify 均 match，无 failures/advisories。

本机 native replace-staged 已成功，接纳时规则仍保持旧摘要；随后新安装入口的显式 codex-agents upgrade 成功。Extra 源 checkout `/home/penn/devel/pennix-skills-extra` 干净且提交保持 `c205b3960602902536ba48bbad5b028803fbf7ab`。没有额外包发布或远端部署。

## 最终验收

- 本机 codex-agents fresh verify 为 `match/current:active`，有效来源 `/home/penn/.codex/AGENTS.md`，无非空 override；源与目标字节相同，新摘要 `819d4dca89d346d3e8bfb5b8fe26702dee5ddc10ed69cc62293f0b97a5d6a281` 与 catalog 相同。
- Pennix 及 Extra 的 scoped fresh verify 均为 `match`、完整性 `match`、无缺失项；Pennix 命令链接及 PATH 均 match，Extra 来源 pin 保持不变。三项核验 failures/advisories 均为空。
- 根新启动 Codex CLI `0.162.1` 只读 ephemeral smoke 成功识别三处新规则与项目边界，未执行工具；源字节、有效来源及模型观察共同核验，不能推导永远遵守规则。根 offline 8/8、回归 6 组及运行器自检 10 项通过。
- 修改模板与本执行记录的中文轻量检查通过；`git diff --check` 通过；三份封口文档摘要保持不变。质量门复用 198 项组件测试，安装行为另由真实隔离和本机入口验收。
- PRD 六项验收均有依据：语义分层、自然落点/局部范围、精确安全迁移、组件检查、已发布原生安装及双集合完整性、独立批准/start 与交付收敛。无阻塞或未决选择。

源交付提交为 `4624ea6229f09516c626a0bb0c8ced2a759f3a84`；后续仅任务记录/归档/journal 提交，不改变集合字节，无需再次重装。回退使用 design.md 已批准的纠正提交路径，原基线 `f89b833` 和本次新摘要明确；不得直接让旧 adapter 覆盖新文件。临时原生日志与 receipt 不提交 Git，完成后只清理本任务所有的临时目录。
