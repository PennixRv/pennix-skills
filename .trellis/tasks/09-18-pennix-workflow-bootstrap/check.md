# 源码验收记录

- `python3 -m unittest discover -s skills/pennix-workflow-bootstrap/tests -p 'test_*.py' -v`：59 项通过。
- `bash -n scripts/seed-arch.sh`、`py_compile bootstrap.py host.py codex_static.py codex_plugins.py`
  和 `skills_install.py`、`git diff --check` 通过。
- 回归覆盖：旧 `plan` 命令被拒绝；`install`/`upgrade`/`uninstall` 都要求具名 component 和 `--yes`；
  static config/AGENTS 的 install/uninstall 幂等；drifted 模板拒绝卸载；package、plugin、Skills collection
  的 native-owner 升级/卸载路径；上游 inspection 在 package manager 前失败关闭。
- `discover`/`verify` 保持只读；未执行真实 host lifecycle 写入，也未替换当前 `/home/penn/.codex`
  安装副本。source collection check、发布和根集成验收在本轮 source commit 后重跑。
