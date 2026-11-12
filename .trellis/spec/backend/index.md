# 集合与评估规范

本目录保存本仓库已经建立的集合交付、文档 Skill、会话交接和评估证据约定。保留 `backend/` 路径以保持实际引用，不据此要求项目采用前后端分层。

## Guidelines Index

| 文档 | 适用内容与源码依据 |
| --- | --- |
| [quality-guidelines.md](./quality-guidelines.md) | `collection.json`、`scripts/collection.py`、文档 Skills、交接脚本和评估入口的质量合同 |
| [logging-guidelines.md](./logging-guidelines.md) | `evaluations/run_codex_cases.py` 的可观察读取结果、来源身份及敏感数据边界 |

## Pre-Development Checklist

- 修改集合成员、Skill、交接或评估入口前，读取 quality-guidelines 中适用的合同及对应源码、测试。
- 修改评估摘要或原生工具轨迹判定时，再读取 logging-guidelines；区分尝试、成功读取和完整消费。
- 安装及锁归 Lifecycle，项目资产归 Trellis 原生入口；本仓库维护集合源码与验证。

## Quality Check

- 运行 `python3 scripts/collection.py verify`，并按改动选择既有 Skill、根侧或评估测试。
- 核对固定来源、许可、成员与命令声明，保留失败、受限和未触发事实。
- 静态合同或安装成功不证明真实模型已选择或完整消费 Skill；真实调用须独立核验并遵守预算。
