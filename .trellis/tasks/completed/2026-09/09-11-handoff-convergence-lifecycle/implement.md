# Handoff convergence lifecycle 实施清单

仅在 task 激活为 `in_progress` 后执行；Codex inline 主会话直接修改、检查、提交。

1. 读取本 task、`AGENTS.md`、applicable specs、handoff scripts/tests 和 routing Skill；冻结 event schema、
   reducer、CLI 参数、runtime paths、confirmation、reason codes；无 fixture 授权时 remote modes 保持
   `unsupported|unavailable`。
2. 在实现 handoff consumer 前先冻结 target session binding 合同：初始 `admit` 只做核对并停住；
   后续明确授权时只复用 Trellis 原生 `task.py start` 或精确 `task.py archive`，读取
   `task.py current --json` 要求直接 `session:<target-key>`，拒绝 `session-fallback`/缺失 identity。
   不在 Pennix Skills 新增 task/session 状态机或手工写 Trellis pointer。
   `source.rollout.session_id` 只进入来源 provenance fixture，必须有回归测试证明它不能通过
   `admit` 变成 target identity；目标绑定证据必须来自已安装 Trellis session-isolation 修复版本的直接
   `session:<target-key>` 解析（最终部署时记录实际发布版本）。
3. 在 `workflow_contracts.py` 集中实现 bounded receipt/attestation/observation validators；在
   `handoff.py` 基于现有 core helpers 增加 CAS append/reducer、prepare/finalize/admit/retention，不能
   改 `write`/`validate` v4 行为或 rollout parser。
4. 更新 renderer、handoff Skill 和 routing Skill；prompt 仍只能在 core ready 且 mode proof 满足时渲染，
   并明确 initial takeover stop。
5. 用临时 project/handoff fixtures 测试：v4 compatibility、receipt CAS/chain、合法状态、idempotence、
   drift、attestation/observation、secret/path/symlink、interrupted writes、copy-first archive、exact
   restore/reopen/purge；另补 target intake/activation/closure 的边界 fixture。不得接触真实
   NAS/OpenViking 或 host runtime。
6. 执行现有 Python tests、适用 lint/security/`trellis-check`、`git diff --check`；若有 GitNexus，完成
   status/impact/detect-changes。失败修根因，否则不提交。
7. 提交并推送 `main`，记录 commit/tests/known limits。用户已明确授权本轮完整部署：两个源码目标验收后，
   运行 `pennix-skills-install` 从当前 checkout 重装宿主副本，并在 `/home/penn/.codex` 更新静态部署记录；
   不写任何 runtime、credential、cache 或 Plugin private state。

## Stop conditions

- v4 core compat、CAS、precise purge、path/secret protection、ready-only rendering 或测试失败时保持原
  core-only 行为；不发布、不写远端、不删 runtime/data。
