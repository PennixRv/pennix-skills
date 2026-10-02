# 封口设计

Planning Seal closed 2026-10-02，已有实施交付授权。

复用native current、append-only receipt、AgentMemoryClient、private配置与Codex native MCP。taskless seal仅无任务core适用，prepare保存canonical source；admit拒绝同source。receipt保存intent/key fact与returned id；重入无id只list恢复，已有id只verify。offset分页100条，最多5页，超界/不唯一明确失败。

既有agentmemory-static目标用Node --env-file、固定0.9.29 npm pair与plugin MCP enabled=false；秘密不复制到TOML。核对现有归属，重入可复现，卸载仅删除本目标资产。官方hooks要求父环境继承及原生信任，当前host需要正确环境重开；FORCE_PROXY不能保证runtime不fallback。scope registry参与proof，同名注册拒绝。无fork、新协议、备份或schema兼容层。
