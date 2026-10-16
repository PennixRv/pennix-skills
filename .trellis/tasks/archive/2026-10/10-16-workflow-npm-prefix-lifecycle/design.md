# 工作流 npm 安装落点与 lifecycle 治理设计

## 行为边界

行为实际位于 `skills/pennix-component-lifecycle/scripts/host.py` 的 npm 命令构造、`scripts/lifecycle.py` 的 catalog 解析、发现、核验和 package operation，以及 `references/component-versions.json` 的组件合同。`SKILL.md` 只补充用户级 npm/AUR/项目依赖边界和迁移顺序说明；不把逻辑放进文档或 shell profile。

## 目标合同

在现有 `package` 元数据中为 npm 组件增加：

- `prefix: "$HOME/.local"`：唯一允许的工作流 npm CLI 目标 prefix；
- `install_owner: "user"`：目标包和入口必须由当前用户持有；
- 可选 `allow_scripts`：只给 Paseo 记录已核验的依赖脚本名，其他 npm 包继续 `--ignore-scripts`。

生命周期将 prefix 展开为当前用户的 `$HOME/.local`，从其 `lib/node_modules` 和 `bin` 观察目标包；同时扫描已知系统和用户 root，形成同一组件的重复安装证据。命令 owner 通过真实解析后的入口和包 `package.json` 核对，文件 owner 通过 `stat` 核对当前用户。

## 迁移顺序

目标安装命令携带 `--prefix $HOME/.local`，并先验证目标版本、入口、owner 和 target prefix。只有目标探针匹配后，才通过旧包实际 prefix 调用原生 npm/pacman owner 删除 `replaces` 或 CodeGraph 的精确旧包；任何失败都保留旧路径和新路径证据并停止。生命周期不改 PATH、SSH、supervisor 或 Paseo daemon；这些由根任务的迁移批次负责。

Paseo catalog 只负责 CLI 包管理和 CLI verify。根任务在最后批次通过 Paseo 原生用户入口重启 daemon，核对 daemon 状态和客户端重新连接。

## 必须修改的文件

- `references/component-versions.json`：npm prefix/owner、Paseo 条目和允许脚本。
- `scripts/host.py`：npm prefix、脚本白名单和旧 prefix 的命令构造。
- `scripts/lifecycle.py`：合同校验、多 root 发现、目标入口核验和安装后清理顺序。
- `SKILL.md`：工作流层全局 npm、AUR/Arch、项目本地依赖和 daemon owner 的边界。
- `tests/test_host.py`、`tests/test_lifecycle.py`：覆盖新增合同和迁移回滚边界。

不修改 FastCtx、Trellis、CodeGraph、CCH 或 Paseo 源码，不复制安装目录，不写用户运行态。

## Revision 2：默认 prefix 配置

用户要求直接注入现有 lifecycle 流程，不新增组件或 configure 子命令。最小修改目标为 `scripts/lifecycle.py`、`tests/test_lifecycle.py` 和 `SKILL.md`；catalog、host 及配置 profile 协议不增加字段。

用户级 npm install/upgrade 在原有主机和包归属前置检查通过后，用原生 npm 读取默认 prefix，必要时仅在用户级作用域设置为 catalog 展开路径并回读核验。已经匹配的包也要检查默认值；默认值已匹配时不重复写入。配置失败阻断后续安装和旧包清理；成功设置的默认值不因后续安装失败而自动恢复。包安装保留显式 prefix，其他 npm 键交给原生 npm 保留，不读取或输出完整配置。

`discover`、`verify`、卸载以及非用户级 npm 操作不写 prefix。Skill 直接说明这一副作用，不新增自动兼容、回退、项目初始化或 shell 修改行为。测试覆盖成功、幂等、回读/写入失败的阻断边界和无关配置保留；根任务承担活动集合重新接纳与真实命令验收。
