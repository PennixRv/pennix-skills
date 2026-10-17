---
name: pennix-component-lifecycle
description: 用户明确要求发现、安装、升级、卸载、配置或核验已登记工作流组件时，使用独立 pennix 生命周期工具；项目初始化仍由目标组件原生入口负责。
metadata:
  short-description: 使用 pennix 管理工作流生命周期
---

# 工作流生命周期

用户明确要求管理工作流组件时，使用已安装的 `pennix` 原生入口。这个 Skill 只负责选择入口、解释结果和守住 owner 边界；组件目录、模板、动作实现和版本固定由 `pennix-lifecycle` 发行物维护，不在 Skill 集合中复制。

## 两阶段部署

新机先运行基础准备脚本。它只准备受支持的 Arch Linux/WSL2 环境、用户级 Python/Kconfiglib/tomlkit、npm 和 `~/.local/bin`，并把 `pennix` 发行物安装到用户目录：

```bash
bash bootstrap.sh
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

`config edit` 和配置文件执行共用 Kconfiglib 模型。`workflow.config` 是带格式主版本标记的 `.config` 键值文件；组件选择使用布尔/choice，路径、URL、数值等自定义内容使用对应字符串/整数项。未知符号、重复或非法值、格式主版本不兼容和依赖未满足必须拒绝并保留原文件。

没有 TTY 时不要让 Agent 代替交互填写。先在受信主机生成或编辑 `workflow.config`，再执行 `pennix plan`、`pennix apply`；缺少必填输入应快速失败。

## 秘密和 owner

使用：

```bash
pennix secrets edit
```

该命令打开用户私有的 `secrets.toml`，以可见文本编辑，保存前由操作者核对。文件权限为 `0600`；秘密不能出现在命令参数、环境变量、任务材料、JSON、差异、日志或回答中。生命周期工具只保存选择和非敏感状态，OAuth、会话数据库、模型认证和组件私有配置由原生 owner 继续管理。

组件的原生入口优先于生命周期包装：

- `trellis init`、Trellis 任务、Channel、交接、Hook 和宿主原生交互继续使用各自接口。
- Codex provider 使用 `codex login`；插件使用 Codex 原生 plugin 命令。
- CCH、Hikari、Grok、Windsurf 和思源的连接值由各自 owner 配置，生命周期只按 catalog 声明的结果做非敏感探测。
- 项目初始化、索引建立和服务端部署必须由目标组件的原生流程完成；系统安装不会替代它们。

## 声明式动作和卸载

`plan` 只读。`apply` 才改变组件、受管模板、npm 用户 prefix、PATH、Paseo user unit 或明确选择的 owner 输入。漂移、未知所有权、符号链接和不安全权限默认停止；使用 `pennix repair <component-id>` 表达显式修复意图。

一次性卸载不改变声明式配置：

```bash
pennix uninstall <component-id> --confirm <component-id>
pennix uninstall --all --confirm-all ALL
```

卸载后配置仍选择的组件会显示为“已选择但未部署”，再次 `apply` 会重新部署。要永久取消组件，先在 `pennix config edit` 中取消选择，再运行 `pennix apply`。反向依赖、受管 relay 条目无法远端撤回、漂移或归属不明时阻塞，不隐式级联。

`--all` 只表示移除当前工具能证明属于自己的已部署工作流目标，不清空 `workflow.config`，不删除用户数据、认证、项目、未知文件或外部维护的远端登记。

## 服务和 relay

Paseo 自启动在配置中明确选择“关闭 / 登录启动 / 无登录常驻”。常驻模式必须具备真实的 user systemd 与 linger 能力；生命周期只管理自己的 unit，不创建 Windows 启动任务，也不关闭未知或共享 linger。服务切换放在其他动作之后，最后验证实际进程和连接。

启用 relay 时，生命周期必须先通过已登记的受信 SSH owner 读取并修改 NAS/router nginx 的精确登记项，完成 `nginx -t` 和 reload，再启用 WSL daemon。relay 仓库文档中的 TLS、`/ws`、Upgrade/Connection 和稳定 `serverId` 规则是唯一反代依据；不得猜测配置、重建 NAS Compose 或为手机新增登记。远端撤回失败时不得开始本地破坏性卸载。Android 配对由用户按 `paseo daemon pair` 的原生输出完成。

## 输出与验证

默认输出应回答当前动作、目标、状态、下一步和阻塞原因；JSON 输出用于脚本化但必须脱敏。`status` 只报告状态，`check` 对已选择目标执行完整非敏感核验，未选择的可选连接不会造成全局失败。真实付费/网络功能测试只有在配置中显式开启时才运行。

不要把“命令存在”“包版本匹配”“配置文件存在”混写成 ready。实际 owner 回执、服务状态、连接结果和用户选择分别保留；无法核验时报告 `blocked` 或 `unknown`。

## 组件边界

`pennix` 是工作流生命周期工具，不是集合源码、组件运行时、NAS 部署器、密钥管理器或 Codex/Trellis 协议模拟器。所有版本、模板、集合来源和动作归属以独立 `pennix-lifecycle` catalog 为准；Skill 不维护第二份成员清单，也不通过多轮 Agent 对话引导安装。
