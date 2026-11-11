# Pennix AgentMemory硬切与正式handoff迁移

## Goal

父09-30-agentmemory-hard-cutover的pennix-skills main实现包；当前planning不改源代码，按父最终design/implement/research13执行，不另建branch。

## Requirements

- 移除活动Hindsight路由/policy/lifecycle/handoff/依赖，保留历史证据，无live兼容/双写。
- 官方plugin0.9.29 hooks/Skills+独立native固定npm MCP/core0.9.29；关闭plugin自带MCP，不改cache、不叠connect --with-hooks，catalog与实际版本/能力探针一致。
- XDG私有client.env经既有zshrc受管入口传新parent，native MCP env_vars转发；秘密不写TOML/argv/Git，无共享全组件.env，FORCE_PROXY=1禁本地fallback。静态资产/秘密各自owner，trust原生执行，verify区分配置与在线可用。
- 仅新建pennix-agentmemory-memory策略Skill，复用官方操作Skills；三层scope/显式promotion/撤销/来源与D11共享派生区别清楚，project登记及启动前override避免basename碰撞，不承诺skills改变父env或ACL。
- 正式handoff按REST remember/memory.id精确read-back，required/core_only、pending/blocked/ready与unknown结果有界reconcile，重复验证不重复写；不新增远端hash门槛。
- 对模型独立协议/同client key实际限制/CCH Provider Body4096补齐给正确指引，不新增relay/rerank功能。Trellis subnode双入口关闭，由Trellis实现，不能靠policy替代。
- 精确清旧本地AgentMemory试接入，再配置新secret；本地Hindsight runtime最终退役需父S4条件，不改共享key/其他组件，原生卸载cache。
- 全实现后统一验证；main提交推送，无版本体系不虚构release，发布源重装及consumer验收完成，根不是源码落点。

## Acceptance

- [ ] current source无活动Hindsight入口，唯一policy/目录/manifest/catalog与最新合同一致。
- [ ] 官方plugin版本/唯一native MCP依赖版本/URL/trust/FORCE_PROXY正确；wrongversion/missingkey/offline明确失败，重入install/upgrade/uninstall无双hooks/MCP/staging。
- [ ] 三层policy与project映射可执行，shared候选不当确认事实；formal handoff完整成功/超时/unknown/并发/重复/近似版本测试通过。
- [ ] 现有unittest/CI/manifest及父统一在线组合验收通过；无secret/cache/NAS模板/根副本。
- [ ] main推送与发布源核验，系统skill-installer/lifecycle用户级重装/verify通过；S4精确卸载Hindsight，无新Authelia或共享key删除，非敏感收据和原生归档完成。
