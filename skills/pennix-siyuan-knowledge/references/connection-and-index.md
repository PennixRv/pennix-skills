# 连接与索引归属
可选的 Lifecycle 连接目标 `siyuan` 配置原生 Streamable HTTP MCP 入口，依赖 `pennix-skills` 集合；它不部署内核，也不启用强制性的知识后端。安装与配置按 `$pennix-component-lifecycle`：首次缺配置时运行 `pennix config init`，已有配置用 `pennix config edit` 选择 `PENNIX_TARGET_SIYUAN` 并设置 `PENNIX_SIYUAN_URL`、`PENNIX_SIYUAN_NOTEBOOK`；经 `pennix plan` 审阅后才运行 `pennix apply`。不再使用旧 discover 或连接目标名。
在目标内核的 `设置 → 鉴权 → API token` 中取得令牌。连接 NAS 内核时，使用 NAS 内核的 Web 客户端，不要使用独立桌面客户端的设置。系统默认会生成令牌，也可以复用已有令牌。它与 Web 登录密码、模型 API 密钥和 S3 凭据相互独立，授予对应内核管理员权限。操作者通过 `pennix secrets edit` 在本机私有中央库填写 `siyuan.api_token`，用 `pennix secrets check` 检查缺失状态；编辑器会显示用户正在编辑的明文，不是隐藏终端提示。不要把令牌输入聊天或argv，不读取配置正文诊断、不复制NAS完整配置；选择性跨机导入仅走Lifecycle已授权的原生秘密入口。
私有归属记录位于 `${XDG_CONFIG_HOME:-~/.config}/pennix-siyuan/connection.json`，目录权限为 0700，文件权限为 0600。记录包含 schema 1、`url`、`api_token` 和 `default_notebook`。原生 `http_headers_helper` 在连接时读取该记录，并直接向 Codex 输出 Authorization 请求头；辅助程序不负责 HTTP、采集或笔记写入。只有 `--metadata` 模式适合诊断。凭据必须留在 Git 之外。`required=false` 允许知识服务不可用时继续普通项目工作。

配置核验检查的是本地归属记录和配置完整性，不等于服务器握手成功。配置后重新连接原生 MCP，并核对实际工具、版本和选定内核；读取笔记本须另符合当前知识访问范围，不能为了验收配置自动读取内容。使用旧工具目录的会话可能需要重启。轮换令牌时通过Lifecycle中央库和原生apply更新自有记录；不要输出header helper内容或普通模式结果来检查令牌。

NAS 与其他思源笔记客户端是彼此独立的内核和工作区。S3 保存同步对象，不是中央 MCP 或共享 SQL 数据库。AI、模型和 MCP 配置属于各自内核；确认每个受影响客户端都经过有意配置。工作流知识使用 NAS 内核，人类客户端继续使用客户端原有的 S3 同步方式。本 Skill 不重配客户端同步。

进行语义读取或写入前，为选定笔记本设置并核验原生 `data/.siyuan/embeddingignore`，然后通过原生设置重建派生向量。规则依赖上游匹配器和真实笔记本 ID，二者都必须核对。对于匹配的上游 gitignore 实现，先排除全部路径，再显式重新包含选定笔记本的后代路径。范围核验完成前，不要调用可能读取其他笔记本的查询。重建会移除旧的派生向量，但不能撤回已经发送给模型服务的内容。保留用户选定的嵌入维度和重排端点。索引维护属于内核所有者操作，不通过 MCP SQL 或直接修改数据库完成。
