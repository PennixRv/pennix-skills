# 合同审查

## 事实

- 归档增强合同要求移除 handoff 的 SHA、snapshot、固定 payload/record/candidate/text/receipt 上限与静默截断，
  保留稳定 handoff id、成对可解析资产、原子发布和既有 lifecycle receipt。
- 发布基线的 `_append_event` 允许同状态追加，且 `lifecycle_admit` 的 successful target 检查只在锁外执行；定向
  两线程测试复现两个不同 target 都 `recorded`。
- renderer 长提示词与短入口均遗漏“读取配对 JSON core”的明确指令；helper 物理读取 core/prompt，但入口合同不完整。

## 决定

- 新 core schema 6 和 receipt v2 不写 digest；旧 schema 4/5 和 receipt v1 只读兼容，历史字段不参与 `ready`。
- 单 target 仲裁复用已有 per-handoff `flock`，不增加服务、锁表或 writer 权限。
- Trellis ownership 仍要求 `--core-digest`；该 digest 仅在 adapter 调其现有接口时即时计算，不写入 handoff core 或
  lifecycle receipt，也不作为语义可信度或消费完整性证明。
- rollout 保留为本地候选投影，但不得复制 raw tool output、限制内容规模或因后续文件漂移否定 package。

## 当前验证

- `python3 -m unittest discover -s skills/pennix-session-handoff/tests -p 'test_*.py' -v`：18/18 通过，包含并发
  target、paired asset、旧 schema、长 capsule 和强 source 状态回归。
- `python3 -m unittest discover -s skills/pennix-skills-install/tests -p 'test_*.py' -v`：10/10 通过。
- `python3 skills/pennix-skills-install/scripts/install.py --source . --check`：已验证 11 个 Pennix Skills。
- `python3 -m py_compile skills/pennix-session-handoff/scripts/*.py` 与 `git diff --check`：通过。
