# 源码验收记录

- `python3 -m unittest discover -s skills/pennix-workflow-bootstrap/tests -v`：65 项通过。
- CI 同形 `find skills -path '*/tests/test_*.py' ... | xargs -0 -n1 python3`：10 个 Python
  Skill 测试模块通过。
- `bash -n scripts/seed-arch.sh`、`py_compile bootstrap.py host.py codex_static.py codex_plugins.py`
  和 `skills_install.py` 通过；`git diff --check` 通过。
- source collection check 在提交 `7129062` 后通过：`Validated 10 Pennix Skills`。
- 隔离 Codex home 验证 seed -> install TOML 可解析、config/AGENTS 模板漂移拒绝、receipt/hash
  rollback 和安装副本包含 `templates/`。
- 根 `node scripts/run-workflow-integration.mjs --full-local --pretty`：13/13 通过。
- `7129062` 已推送到 `origin/task/fastctx-guidance-release`；本轮未替换当前 `/home/penn/.codex`
  安装副本，也未执行真实 host apply，因此 apply receipt 和新会话验证仍是后续部署验收项。
- 当前主机的只读 plan 已复核：package conflict、npm inventory/命令不一致、未发布 npm candidate 都是
  `blocked`，不是可执行 action；缺少 CCH/Hikari 时是 native-owner plan-only，不猜端点或凭据。
