# Retention Pair 审查

## 已核验事实

- `lifecycle_admit()` 在 successful receipt 前解析 core、读取 paired prompt，并在同一 per-handoff lock 内仲裁
  successful target。
- 当前 `_archive_copy()` 只在 canonical prompt 存在时才复制；`_archive_snapshot()` 也容许 archive 只有 core。
  `lifecycle_retention(restore|reopen|purge)` 会使用 snapshot，但 canonical 不存在时的 `lifecycle_status()` 直接
  验证 core，因此也接受不完整 archive。
- 当前 Skill 合同明确写明 retention archive 原子复制并检查 core 与 paired prompt；现有测试只断言正常 archive
  具有 pair，未覆盖 admission 后 prompt 丢失或残缺 archive。

## 回归证据

`python3 skills/pennix-session-handoff/tests/test_handoff.py HandoffTests.test_lifecycle_archive_purge_restore_and_session_provenance`
在新增的 canonical prompt 删除场景失败：`retention archive` 的返回码为 `0`，而断言要求 nonzero。失败发生于
`test_handoff.py:358`，证明该路径确实会保留只含 core 的 archive，不是静态推测。

## 决定

完整 pair 是 retention 可恢复性合同，而非内容真实性或语义可信度门槛。用已有普通文件/readable 检查修复；
不引入 digest、长度限制、追加 receipt event、自动恢复或远端状态。

## 下一步

令 `_archive_snapshot()` 要求精确 pair，令 `_archive_copy()` 无条件读取/copy canonical prompt，令 archive-only
`lifecycle_status()` 调用 snapshot；恢复也无条件尝试从已验证 archive prompt 补回 canonical prompt，避免 snapshot
之后的缺失被静默跳过。随后运行完整组件回归与安装检查。

## Bug Analysis: retention 将 paired prompt 误作 optional

### 1. Root Cause Category

- **Category**: D/E - Test Coverage Gap / Implicit Assumption。
- **Specific Cause**: admission 的完整读取被错误地当作 archive 阶段仍可假定成立的条件；`_archive_copy()` 与
  `_archive_snapshot()` 分别把 prompt 包在 `exists()` 分支，且 archive-only `status` 只解析 core。既有正常
  archive 测试没有破坏 pair，因此没有暴露合同与实现的偏差。

### 2. Why Fixes Failed

无先前失败修复。本次先以定向回归证明现状，再在所有 retention consumer 共用的 snapshot/copy 边界修复，避免为
archive、restore、status 分别添加临时检查。

### 3. Prevention Mechanisms

| Priority | Mechanism | Specific Action | Status |
| --- | --- | --- | --- |
| P0 | Test Coverage | lifecycle 端到端回归删除 canonical/archived prompt，验证失败不追加 receipt、修复后可独立重试 | DONE |
| P0 | Architecture | `_archive_snapshot()` 以精确 core/prompt 文件集合成为 archive 读取的共同前置条件 | DONE |
| P1 | Documentation | 既有 `pennix-session-handoff/SKILL.md` 已明确 archive 复制 paired prompt；不向 root 通用 spec 重复组件实现合同 | DONE |

### 4. Systematic Expansion

- **Similar Issues**: `restore`、`reopen`、`purge` 和 archive-only `status` 都经 `_archive_snapshot()`；此次 shared
  guard 已覆盖。renderer 的 paired prompt 在 canonical package 路径独立验证，现有 renderer tests 保持通过。
- **Design Improvement**: 不增加 digest、第二 receipt 或 archive health 状态。完整 pair 是可恢复资产的最小结构，现有
  ordinary-file/readable 验证足够表达该合同。
- **Process Improvement**: 修改 lifecycle artifact 时必须在同一端到端 fixture 覆盖“成功路径”和“成功后资产缺失”的
  可重试失败路径。

### 5. Knowledge Capture

- [x] `pennix-session-handoff/SKILL.md` 的现有 paired archive 合同仍准确，无需改变。
- [x] 最小回归和任务研究保存根因与修复边界。
- [x] 不创建根仓库 spec/issue：实际修改目标是组件仓库，通用化该内部合同会违反载体边界。

## Verification Before Release

- 定向 lifecycle 回归：通过。
- `python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py' -v`：18/18 通过。
- `python3 -m unittest discover -s skills/pennix-skills-install/tests -p 'test_*.py' -v`：10/10 通过。
- `python3 -m py_compile skills/pennix-session-handoff/scripts/*.py`、`git diff --check`：通过。
- `python3 skills/pennix-skills-install/scripts/install.py --source . --check`：验证 11 个 Pennix Skills。
