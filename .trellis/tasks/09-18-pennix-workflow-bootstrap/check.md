# 源码验收记录

- `python3 -m unittest discover -s skills/pennix-workflow-bootstrap/tests -v`：46 项通过。
- CI 同形 `find skills -path '*/tests/test_*.py' ... | xargs -0 -n1 python3`：10 个 Python
  Skill 测试模块通过。
- `bash -n scripts/seed-arch.sh`、`py_compile bootstrap.py codex_static.py`、
  `skills_install.py --source . --check` 和 `git diff --check` 通过。
- 隔离 Codex home 验证 seed -> install TOML 可解析、config/AGENTS 模板漂移拒绝、receipt/hash
  rollback 和安装副本包含 `templates/`。
- 根 `node scripts/run-workflow-integration.mjs --full-local --pretty`：13/13 通过；发布后安装
  结果追加到本文件。
