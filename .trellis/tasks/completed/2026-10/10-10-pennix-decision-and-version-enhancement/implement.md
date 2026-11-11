# 实施与部署顺序

## Gate

当前保持 planning，等本任务当前 sealed revision 获得明确批准后再 approve/start。开始前读取该 Skill 与 lifecycle 规范，核实 main HEAD、catalog、当前已安装 receipt、Trellis 已发布配对版本和 tmux 官方仓库/本机实际版本。任何版本或 owner 变化先回根任务记录并判断是否需要 replan。

## Ordered work

1. 编辑 decision grill Skill：按 D15 补原始需求/主线未决项的封口核对，按 D01 补额外发现范围选择，旁线确定落点后回主线；编辑中文技术写作 Skill/载体参考、decision-grill contract tests 和 Pennix 自有 guide copy。检查差异只包含本任务目标，回读 Trellis 资产案例，确认固定骨架与自定义正文已分层。
2. 更新 tmux pin 到 3.8；Trellis `trellis-cli` pin 等配对 beta 发布并经 npm 核验后再更新。同步必要 lifecycle fixture/预期版本测试。
3. 执行 decision-grill 合同测试、lifecycle catalog/verify 测试和 Pennix 全集合适用检查。确认 catalog 格式、唯一来源和现有 pinned mismatch 行为未变。
4. 按仓库约定提交并推送 `main`；不 blanket-stage 不相关任务记录或缓存。
5. 新建 staging 并通过原生 `$skill-installer` 安装已推送集合；核对 Skill 清单与 `seed-arch.sh` 执行权限，再按 lifecycle 原生 `replace-staged` 更新活动集合。随后跑 `discover`、`verify --component trellis-cli`、`verify --component tmux` 与完整 `verify`。
6. 通过 `$pennix-trellis-project-update` 刷新 Pennix 项目生成资产；处理 `.new` 或其他受保护候选时仅按任务 owner 接受本计划包含的改动，运行原生 update dry-run 确认落点。
7. 将提交 SHA、发布版本、安装 receipt/验证结构化结果和项目更新证据回写本任务及根协调任务；等待根侧集成验收后再原生 finish/archive。

## Rollback

通过已推送 Git SHA 回退源 Skill/catalog，并再次使用 `$skill-installer` staging、receipt 与 `replace-staged` 原生重装。Trellis pin 回到上一个已发布配对版本。tmux 服务/包不动；如果官方候选在实施时不同，则停止并回到用户决策，不自动降级或改政策。项目资产只通过原生 update 回退并保留本地差异。
