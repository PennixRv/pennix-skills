# 实施前源码验证

## 真实性与修改落点

两个根任务的历史证据分别核验：无身份的 FastCtx transport 失败属实；正确原生 Trellis 身份/绑定/启动的 bug 未复现。语义代码编辑历史误用未证实；FastCtx 包装 task.py 的实际偏离及上层入口遗漏 apply_patch 分支得到确认。

实现只改四处 pennix-skills 源码：两份路由 SKILL、lifecycle AGENTS 模板和它的 catalog revision。未改变运行时行为、Hook、身份信任、工具 schema、配置参数或 SSH 拓扑。

## 已通过

- pennix-workflow-routing 既有合同：6 项。
- pennix-fastctx-routing 既有合同：3 项。
- lifecycle 完整 Python 测试：136 项，包括静态模板、collection receipt 和受管替换。
- 三份相关 Skill quick_validate。
- git diff --check。
- 当前实际原生 select 与三项 task seal/approve/start 成功，均由宿主可信身份绑定；没有伪造 env/session/pointer。

无需为文字变更新增仅匹配新文案的测试。上述既有静态合同检查只防文案/资产遗漏，不证明未来模型必然服从路由。安装发布验收在 deployment.md 中追加。源集合以 GitHub main 的实际提交发布，无独立 npm 包或语义版本号。

