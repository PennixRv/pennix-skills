# Pennix实施与发布计划

当前planning，父任务最终seal与实施启动前不写源代码；主会话inline，目标main，无新branch。旧Hindsight两任务已归档，不重复执行。

1. 原生start、确认main与remote/工作树，trellis-before-dev读取本repo specs；以现有catalog/adapters/test为基础。
2. 更新lifecycle catalog、codex_plugins/configuration/安装适配，官方plugin MCP policy关闭、固定npm shim/core与lock验证、native MCP env_vars、XDG私有env/受管zshrc/receipt与project登记；保留其他组件/用户配置。
3. 更新workflow-routing及唯一pennix-agentmemory-memory policy；正式handoff脚本/schema/receipt/test按REST精确读回合同改为AgentMemory，移除Hindsight活动Skill/adapters/dependency，不全局替换历史文字。
4. 同时实现必要回归：版本漂移、trust/offline/missingkey、MCP重复/manifest占位、不同clientkey不可用、原生body4096、三层语义、handoff超时重入/并发/近似版本、staging清理/受管卸载。不要新增镜像源码/配置副本。
5. 全owner实现齐全后按父统一矩阵运行：python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -v；python3 -m unittest discover -s skills/pennix-session-handoff/tests -v；全CI现有find/sort/xargs逐test_*.py执行；git diff --check及已有manifest/schema验证。不引入pytest。隔离CODEX_HOME演练安装/卸载/重装；真实NAS+主/子会话组合验收不能由mock替代。
6. 全必需项通过才提交推送main；本repo无独立语义版本release，不编造发包。Trellis发布后更新唯一catalog至实际验收beta版本/source，受影响检查后提交推送最终main；remote确认后系统skill-installer+guided lifecycle重装用户资产，逐组件discover/select/upgrade，不修改cache。
7. 新launch原生trust完成后fresh-verify，证明只有官方hooks/Skills+一个native MCP且版本精确、URL正确、Hindsighthook持续关闭。父完成所有消费者验收后硬卸载Hindsight用户级plugin/hooks/config/token/runtime；共享API/provider key不删除。记录不含秘密收据并归档。

配置错误同一路线修复；新事实改变材料边界原生replan，不用二次问已批准发布/重装。当前回合不执行上述步骤。
