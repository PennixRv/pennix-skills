# Retention Pair 合同

`admit` 已读取 canonical core/prompt 并成功写入 `target=reconciled` 后，retention 是独立步骤；它不允许
以较弱的完整性语义保存资产。现有 archive 目录的有效文件集合因此严格为：

```text
session-handoff.json
session-handoff-prompt.md
```

| 操作 | 缺 prompt 的结果 | receipt 结果 |
| --- | --- | --- |
| `retention archive`，canonical 缺 prompt | `ContractError`，不发布 archive | 保持 `archive_eligible` |
| `retention archive`，已存在 archive 缺 prompt | `ContractError` | 不改写 |
| `restore` / `reopen` / `purge`，archive 缺 prompt | `ContractError` | 不改写 |
| `status`，canonical 已删除且 archive 缺 prompt | `ContractError` | 不改写 |

实现只将 prompt 从 optional 改为既有 `_regular_file`/UTF-8 readable 前置条件，并让 archive-only `status`
复用 `_archive_snapshot`。没有新的 lifecycle 状态、事件字段或独立 validator。
