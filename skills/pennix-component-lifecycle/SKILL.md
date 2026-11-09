---
name: pennix-component-lifecycle
description: 用户明确要求发现、安装、升级、卸载、配置或核验已登记工作流组件时，使用独立 pennix 生命周期工具；项目初始化仍由目标组件原生入口负责。
metadata:
  short-description: 使用 pennix 管理工作流生命周期
---

# 工作流生命周期

用户明确要求管理工作流组件时，使用已安装的 `pennix` 原生入口。这个 Skill 只负责选择入口、解释结果和守住 owner 边界；组件目录、模板、动作实现和版本固定由 `pennix-lifecycle` 发行物维护，不在 Skill 集合中复制。

## 两阶段部署

新机使用已核验的固定发行。以下 `v0.2.28` bootstrap 准备受支持的 Arch Linux/WSL2 环境和工具运行依赖，把 `pennix` 安装到用户目录；组件安装由后续工具动作负责：

```bash
curl --proto '=https' --tlsv1.2 -fsSLo /tmp/pennix-bootstrap.sh https://github.com/PennixRv/pennix-lifecycle/releases/download/v0.2.28/bootstrap.sh
bash /tmp/pennix-bootstrap.sh install --release v0.2.28
```

准备完成后，所有工作流配置和组件动作由同一个工具处理：

```bash
pennix config init
pennix config edit       # 有 TTY 时使用中文全屏菜单
pennix config check      # 无 TTY 或 CI 使用已保存配置
pennix plan              # 只读生成动作计划
pennix apply             # 按计划执行
pennix status
pennix check
```

`config edit` 和配置文件执行共用 Linux Kconfig 模型。`workflow.config` 是带格式主版本标记的 Kconfig 值文件；选项使用 bool/choice，ID、URL 和路径等数据使用 string，容量使用有范围的 int。未知、重复、互斥冲突、非法值、格式主版本不兼容和依赖未满足必须拒绝并保留原文件。无 TTY 部署可直接编辑该文件，无需运行 `config edit`。

新机可以用发行物唯一的 `config/defconfig-wsl` 经 `config init --defconfig <路径>` 生成公开默认配置；主机专属普通值仍在目标机的
`workflow.config` 中填写。交互菜单读取文件值作为默认并允许覆盖，非交互部署直接使用文件值。

没有 TTY 时不要让 Agent 代替交互填写。先在受信主机生成或编辑 `workflow.config`，再执行 `pennix plan`、`pennix apply`；缺少必填输入应快速失败。

当前目标为 Arch Linux / WSL2 Arch x86_64、同设备同用户单个管理目标，允许非默认 CODEX_HOME。跨设备只带配置意图，目标机重建锁、receipt、journal 和秘密；改变 XDG_STATE_HOME 不能绕过已有目标登记或事务。bootstrap 的系统准备包含完整 `pacman -Syu`，按实际计划及既有授权执行。

## 秘密和 owner

使用：

```bash
pennix secrets edit
pennix secrets --help
pennix secrets import-ssh --help
```

`secrets edit` 打开用户私有的 `secrets.toml`，以可见文本编辑，保存前由操作者核对。文件权限为 `0600`；秘密不进入任务材料、差异、日志或回答。秘密文件只保存凭据，URL、ID 和路径属于 `workflow.config`。Codex provider 使用自定义 Responses API URL 与静态 API Key；运行时由生成的 `auth.command` 按工具原生合同读取私有 Key，不调用 `codex login` 或要求 ChatGPT 登录。其他组件凭据由各自 owner 接收。OAuth、会话数据库和 daemon 身份继续由原生 owner 管理。

已有可信 SSH alias 时，按 `pennix secrets import-ssh --help` 选择服务，导入固定 owner 凭据字段。它不复制整份认证、不带入 URL/ID/路径，也不执行任意远端命令；手工填写秘密文件仍是等价路径。参数以当前原生 help 为准，Skill 不复制秘密子命令协议。

组件的原生入口优先于生命周期包装：

- `trellis init`、Trellis 任务、Teamwork、交接、Hook 和宿主原生交互继续使用各自接口。
- Codex provider 的 URL、模型和偏好由 owner 按当前 CLI 配置接口更新；静态 Key 只走上述 `auth.command` 读取接口。插件使用 Codex 原生 plugin 命令。
- CCH、Hikari、Grok 和思源的秘密从 `secrets.toml` 交给各自 owner；Windsurf 默认兼容中央输入，也可明确开启 `PENNIX_WINDSURF_OWNER_CREDENTIAL`，由其原生 owner 使用专属文件，缺文件时从既有 Devin 登录导入，不新增中央副本。环境覆盖、外部文件、漂移或不安全权限仍阻断。未选连接保持关闭，状态输出不回显凭据。
- 项目初始化、索引建立和服务端部署必须由目标组件的原生流程完成；系统安装不会替代它们。

## 声明式动作和卸载

`plan` 只读。`apply` 按 `components.lock.json` 中的已核验目标改变已选择组件和 owner 输入，普通 `apply` 不升级已有锁；明确升级使用 `pennix update <component-id>`，由原生入口展示精确候选和影响并确认。漂移、未知所有权、符号链接和不安全权限默认停止；使用 `pennix repair <component-id>` 表达显式修复意图，参数以当前 help 为准。当前未实现原生写入接口的连接目标会阻断 `apply`，不能把输入齐全当成连接已配置。

Arch/AUR 外部更新或已启用 Codex 插件与锁失配时，使用 `pennix reconcile <component-id>` 展示并接受精确已安装身份。它要求可信旧记录与同源核验；系统包只同步记录，插件只通过原生 Marketplace 对齐，不自动升级、降级或编辑缓存。部分失败保留 journal，恢复必须沿相同原生入口重新核验。`outdated` 仅表示实际身份与锁不相等；结合实际身份、锁定身份与既有受管记录判断。

先用 `pennix recover --json` 查看未结事务，再按当前原生 help 对同一事务和步骤处置。none、restored 或完成后置条件必须有原生证据；版本相同、人工确认或干净工作树不能释放 unknown。没有 force 清除入口；所有处置留存归档，不自行改写状态文件。旧 owner 缺少 validate/事实协议时先明确升级，普通 apply 不偷偷追最新。

一次性卸载不改变声明式配置：

```bash
pennix uninstall <component-id> --confirm <component-id>
pennix uninstall --all --confirm-all ALL
```

卸载后配置仍选择的组件会显示为“已选择但未部署”，再次 `apply` 会重新部署。要永久取消组件，先在 `pennix config edit` 中取消选择，再运行 `pennix apply`。反向依赖、受管 relay 条目无法远端撤回、漂移或归属不明时阻塞，不隐式级联。

`--all` 只表示移除当前工具能证明属于自己的已部署工作流目标，不清空 `workflow.config`，不删除用户数据、认证、项目、未知文件或外部维护的远端登记。

生命周期工具自身卸载使用其 bootstrap 的 `uninstall` 操作；这与工作流组件卸载是不同入口，均须保留原生归属与数据保护检查。

`pennix-skills` 和 `pennix-skills-extra` 各自维护 `collection.json`，声明成员路径、许可、命令和物化来源。`pennix-lifecycle` 固定集合仓库提交并独立验证 manifest；Skill 集合不复制 lifecycle catalog。receipt、集合树和命令链接必须一起切换，升级失败恢复旧树；损坏、未知或不受支持的 receipt 一律阻塞，不读取历史格式。

## 服务和 relay

Paseo 自启动在配置中明确选择“关闭 / 登录启动 / 无登录常驻”。登录自启只在 systemd 用户 manager 启动时执行一次原生 `daemon start`；日常启停使用 `paseo daemon start/stop/restart`。`PENNIX_PASEO_RUN` 只请求本次 apply 显式启动，自启无需开启该项。普通检查和 apply 不拉起已停止实例，关闭或移除入口不停止 daemon；入口配置、实际运行健康和版本分别核验。常驻模式必须具备真实的 user systemd 与 linger 能力；生命周期只管理自己的 unit，不创建 Windows 启动任务，也不关闭未知或共享 linger。服务切换放在其他动作之后，最后验证实际进程和连接。

官方 Skills 首装由已验证版本的 Paseo 公开接口自动完成；计划须披露 `.agents/skills`、`.claude/skills` 及原生自有旧 `.codex/skills` 的影响。停止态 daemon 只为安装临时启动，按同一实例停止；安装、启停或连接结果不明时保留现场，不盲目重放旧前台启动。以原生 selection、manifest、磁盘和实例事实核验结果，不能把 selection=all 当成安装完成。

启用 relay 时，生命周期必须先通过已登记的受信 SSH owner 读取并修改 NAS/router nginx 的精确登记项，完成 `nginx -t` 和 reload，再启用 WSL daemon。relay 仓库文档中的 TLS、`/ws`、Upgrade/Connection 和稳定 `serverId` 规则是唯一反代依据；不得猜测配置、重建 NAS Compose 或为手机新增登记。远端撤回失败时不得开始本地破坏性卸载。Android 配对由用户按 `paseo daemon pair` 的原生输出完成。

## 输出与验证

默认输出应回答当前动作、目标、状态、下一步和阻塞原因；JSON 输出用于脚本化但必须脱敏。`status` 只报告状态，`check` 对已选择目标执行完整非敏感核验，未选择的可选连接不会造成全局失败。真实付费/网络功能测试只有在配置中显式开启时才运行。

不要把“命令存在”“包版本匹配”“配置文件存在”混写成 ready。实际 owner 回执、服务状态、连接结果和用户选择分别保留；无法核验时报告 `blocked` 或 `unknown`。

## 组件边界

`pennix` 是工作流生命周期工具，不是集合源码、组件运行时、NAS 部署器、密钥管理器或 Codex/Trellis 协议模拟器。组件动作、模板和集合仓库由独立 `pennix-lifecycle` catalog 声明，动态安装目标由原生锁和回执固定；集合内部成员和物化来源由各自 manifest 声明。Skill 不维护第二份成员清单，也不通过多轮 Agent 对话引导安装。
