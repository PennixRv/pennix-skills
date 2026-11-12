# 交接资源生命周期实施证据

根合同与用户批准已在本任务 PRD 固定；实施进度、故障、验证和未结项只追加本文件，不修改已接受合同。

初始 source HEAD `fe7b0ebfff0be46349265bc3b7e357f109ef8df0`。当前 helper 为 schema 12，旧 retention 复制展开目录、receipt 锁在 JSONL inode，历史读取依赖当前 schema；本包按已接受根合同收敛这些边界。尚未修改正式交接资产，未调用 pending next action。

原生目标接受曾拒绝错误 outcome 参数 requirements_confirmed；读取实际状态后改为 accepted，设计接受、授权、start 已成功。没有手写阶段或身份。

候选已有 handoff_storage.py 的流式 ZIP、逐成员 SHA、私有权限、受约束解压、旧源映射及固定 handoff.lock；只读历史/inspect 与严格当前准入分开。新增底层 6 项和首批 retention 4 项端到端通过。包内 retention-events.jsonl 是精确存储操作及恢复定位的持久证据，不授予或复制 Task authority；原 lifecycle 和旧原始字节保持前缀。归档发布后镜像失败已能读出提交事实并幂等修复。

仍须完成 purge 故障和恢复、并发变更、旧 ownership/唯一旧 archive、原生 renderer/Skill/根调用者、完整资源门与集合验收。旧回归两处硬编码 runtime receipt 和旧 ID-only 直接删除语义待同步；本候选尚未达到整体验收、发布或安装条件。真实历史未迁移或删除。

## 完整候选验证与恢复检查

上述旧回归和调用者已同步。全交接测试首轮 74 项通过（资源门默认跳过 1 项）；随后追加原生 recovery_history 对旧 claim intent 的围栏检查，retention 13 项通过。独立资源门实际运行 829.958 秒，1k/10k/100k 与 8 MiB 长记录共 76 次操作全部成功，峰值 RSS 95.703125 MiB、临时盘 681.575654 MiB、单次最长 75.606 秒，未缩小门槛。原始测量保存在私有 /tmp，未进入 Git。

新增失败覆盖包括 archive 提交后镜像失败、purge 目录切换/部分删除/最终发布失败、restore 发布失败、未知 tombstone 成员、原生 Task 成功而本地收据失败、明确 CAS 拒绝清除本次 intent、release 只读结果恢复及旧目标被原生恢复围栏后的接续。跨 owner RPC 期间固定 handoff 锁可由其他进程取得。当前 prompt 在保留前校验，ZIP manifest 操作与保留日志绑定。恢复和历史读取均不重授 Task authority。

collection verify 为 19 Skills、2 commands；根测试 15 项和离线评估 driver 已通过。全集合测试及根组合验收继续核验。尚未发布、更新安装或处置真实历史。
