# Pennix AgentMemory合同

源码仅pennix-skills main；根协调任务最新design、implement、research13为cross-owner合同。替换Hindsight活动入口，不复制NAS/router配置、上游plugin源码/cache或Trellis runtime。

## 固定组件与唯一接入

唯一catalog references/component-versions.json声明官方marketplace/plugin0.9.29、npm MCP/core0.9.29、iii0.22.1服务合同。扩展已有scripts/adapters/codex_plugins.py、configuration.py、skills_install.py及相关hook/config机制，不另建部署框架。官方plugin保留hooks/Skills，native plugin policy禁其自带MCP（shell占位不被Codex解析且npx浮动）。独立Codex mcp_servers.agentmemory：node启动XDG私有npm目录node_modules/@agentmemory/mcp/bin.mjs；原生npm同时安装shim/core精确版本，package-lock与npm依赖树验证。禁止connect codex --with-hooks叠加。

私有~/.config/agentmemory/client.env供zshrc受管块source，向新parent提供URL/newsecret/FORCE_PROXY=1/INJECT_CONTEXT=true，native MCP env_vars转发并允许per-launch PROJECT_NAME。不在TOML/argv/Git放secret，不把LLM upstream key分发客户端，不创建全组件.env。使用已有XDG state namespace管理非敏感receipt，不重现~/.codex/pennix-workflow-lifecycle。重装需新Codex launch/resume与原生trust，verify明确区分配置存在、已启用、在线可用；trust不能自动伪造。

## 策略、身份与三层语义

仅新建pennix-agentmemory-memory，删除pennix-hindsight-memory活动Skill，routing保持owner-native不被FastCtx包围。复用官方操作Skills；正式session-handoff是独立用户意图，不路由到上游记忆handoff。

项目默认唯一git basename；私有XDG config/agentmemory/projects.json登记root/worktree↔logical project，显式project绑定独立于系统安装，遇同名/改名/工作树需启动前env override，不全局固定project、不承诺Skill改变已运行hookenv。项目raw session/摘要/observations按来源校验；D11允许共享派生/lessons候选。确认知识显式project=pennix-knowledge；用户确认偏好project=pennix-user-penn、type=preference；content记录原项目/来源/时间/确认，撤销精确id。自动派生不等于确认知识；单key不是多租户ACL，recall无project不能用于精确事实验证。槽位/图谱/远程重排不新增。

## 正式handoff

scripts/hindsight.py与测试替换为agentmemory.py/目标测试，不保留live兼容。core/capsule权威及既有本地一致性不变，明确agentmemory_required/core_only。stdlib REST POST /agentmemory/remember(type workflow/project/content含包标识+capsule)检查success+memory.id，原子receipt记id，GET /agentmemory/memories/:id逐值核对才ready；远端新sha256门槛不新增。

重复validate只读已有id。POST未知结果按project/type/limit100/cursor最多5页精确匹配包标识/content，唯一可复用，其他pending不盲POST；不符blocked，服务离线pending，core_only显式注明。server supersession不能替代旧包id/content，记忆读回不等LLM派生，也不从搜索/召回推导ready。历史旧包保留审计，不引入运行时兼容。

## 删除与重入

旧AgentMemory试接入先原生卸载、精确清专属env/config/MCP/hooks，不手工cache；共享keys/历史证据保留。Hindsight新活动代码在实现阶段删除；真实NAS/runtime仅父S4批准条件满足后删除。lifecycle重复install/configure/upgrade/uninstall/verify不双hook/MCP、不留staging；wrongversion/missingenv/offline/filterdrift分别可见，不报假成功。Trellis subnode必须整体plugin+native MCP均关闭，Pennix不以Skill替代进程控制。
