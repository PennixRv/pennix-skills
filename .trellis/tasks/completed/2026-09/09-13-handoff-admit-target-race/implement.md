# 实施

1. 删除 handoff core、rollout projection、observation 和 lifecycle receipt 中仅用于旧投影的摘要、快照和固定
   容量门槛；保留路径安全、可解析 JSON、秘密防护、原子发布及状态转换。
2. 将新 core/receipt schema 升级为无摘要形式，并保持对既有 schema 的读取兼容；ownership 调用单独适配
   Trellis 既有 `--core-digest` 接口，不扩散其语义。
3. 在 `_append_event` 的已有锁中执行 `reconciled` target 重检；用并发测试直接覆盖唯一提交点。
4. 修正 long/short renderer 指令，使 paired JSON core 与 prompt 是同一完整消费要求。
5. 运行定向与完整 Skill 测试、安装器检查、源/安装副本一致性检查；提交、推送并官方重装。
