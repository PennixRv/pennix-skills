# 实施顺序

1. 在现有 lifecycle fixture 加入 canonical prompt 丢失后 archive 失败/修复后重试成功的回归。
2. 在同一 fixture 加入 archive prompt 丢失后 status/restore 均拒绝的回归，确认 receipt 不增长。
3. 让 `_archive_snapshot` 要求完整 pair，`_archive_copy` 无条件读取/copy canonical prompt，archive-only
   `lifecycle_status` 调用 snapshot。
4. 运行 handoff/renderer、安装器、编译、source check；审查差异，提交推送并官方重装。
