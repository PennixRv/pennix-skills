# 源码验收记录

- `python3 -m unittest discover -s skills/pennix-workflow-bootstrap/tests -v`：65 项通过。
- CI 同形 `find skills -path '*/tests/test_*.py' ... | xargs -0 -n1 python3`：10 个 Python
  Skill 测试模块通过。
- `bash -n scripts/seed-arch.sh`、`py_compile bootstrap.py host.py codex_static.py codex_plugins.py`
  和 `skills_install.py` 通过。source collection check 与 `git diff --check` 在 source commit 后重跑，
  因为安装器拒绝未提交 checkout。
- 隔离 Codex home 验证 seed -> install TOML 可解析、config/AGENTS 模板漂移拒绝、receipt/hash
  rollback 和安装副本包含 `templates/`。
- 根 `node scripts/run-workflow-integration.mjs --full-local --pretty`：13/13 通过；发布后安装
  结果追加到本文件。
- 当前主机的只读 plan 已复核：package conflict、npm inventory/命令不一致、未发布 npm candidate 都是
  `blocked`，不是可执行 action；缺少 CCH/Hikari 时是 native-owner plan-only，不猜端点或凭据。
