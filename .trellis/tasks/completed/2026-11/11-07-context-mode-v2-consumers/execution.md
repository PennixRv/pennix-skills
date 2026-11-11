# 执行记录

- 原生规划 revision 1 / digest `sha256:95a85ede1274211e8f8ef14977be73d9417c0063c0883bcbf9b3d4f85164cfa0` 已 seal/approve/start。批准依据为根任务已展示方案和用户明确继续指示，未新增选择；没有 open decision，按原生接口从 solution_formation 直接进入 solution_review。
- 分支 refactor/context-mode-v2-consumers，起点 5cfe7adb61ddd585a6f65574b5aec6fb1c6c3c49。已删除集成成员，修订 manifest、AGENTS、路由、CodeGraph、清理边界和评估；保留 cases 的 skills_before 旧名称作为基线事实。
- collection verify：15 Skills / 2 commands；路由 5 项、runner 10 项、根 tests 12 项通过。runner 支持显式 CODEX_HOME 和固定集合提交，实际树摘要必须吻合 Lifecycle receipt；phase 仍只是结果标签。
- 待做：真实 owner 物化的 before/after 评估、必要 spec、源码与公开提交、owner 更新移除旧成员及根集成；不以静态通过代替真实行为。

- runner 后续去掉 ephemeral：v2 原生线程元数据需要真实 rollout，已有 spec 也明确 ephemeral 无 rollout 时 Hook 可全部拒绝。评估历史仅留隔离临时 CODEX_HOME，不进入 Git；compact/reload 仍由真实组件 app-server 验证，不以单轮测试代替。provider 只复用公开设置和现有 Lifecycle auth command 的运行时输出，不复制私有认证文件。

- 实际 before/after 评估累计 20 轮，原始 rollout 和 stderr 仅保留隔离临时现场。before 的旧 MCP approval deny 未绕过；首轮 after 因 MCP 子进程未收到 CODEX_HOME 而失败，随后由 Lifecycle 配置修正。重跑又发现 24 KiB 路由入口触发上游 16 KiB 单次读取限制，部分模型误当权限拒绝。保留失败结果，按渐进披露将阶段、代码检索、协作和专项 owner 细节移入有触发条件的 references，入口保留基本路由、权限和全文边界，没有改上游 Hook。
- 最终行为候选 `9f9cb2180858b824db816f23cf49b61598fc983d`，owner 物化集合摘要 `aecf38c3308ecd468a9e833727d9475e898ab6075a7842a3ef8dba5aebd25923`。第 016–020 轮 S04-positive、S04-boundary、C01、C09、C10 均实际完整读到声明的 Skill，路径未猜测；MCP ctx_resume 均成功。小文件允许原生读取/rg，1000 行全文通过连续原生分页取得；C01 本地检索和真实 CLI help 完成。C10 ctx_execute 成功读取并匹配，未触发失败回退，不能宣称失败分支经过这轮实测。
- 路由 5 项、评估 runner 10 项、集合根 12 项及 collection verify 15 Skills / 2 commands 通过；Skill validator 通过。后续任务记录改动不改变已验收成员树。还需公开提交、真实 owner 更新与跨仓安装验收，不提前归档组件任务。

- 交付复核：公开提交 `0b8a1c6384bca4e527cf9824eabd0a4eb69c2a93` 已经真实 pennix update 安装，native status 为 match；旧集成 Skill 目录已不存在。Lifecycle 最终使用 `0.2.36`，CM 为 `2.1.5-pennix.1`；四个实际 Hook trusted，AOE trusted 状态保留。根 full-local 19 项全通过，根测试 8 项及 offline 11 项通过。Trellis backup list/prune 的本仓结果均为空，没有失败或保护对象。
- 复发预防：本次缺口属于跨层合同与测试覆盖不足。旧单入口承载大量条件规则，超过上游读取阈值后提示又被模型误当权限拒绝；已拆分条件引用并实测完整首读。来源标签不足以证明候选，runner 现核验实际 receipt 与成员树。相关可执行评估合同写入 backend quality spec；安装配置与 trust 迁移经验归 Lifecycle 文档，不复制到本仓。后续提交仅为规范和任务记账，不改变已安装成员树。
