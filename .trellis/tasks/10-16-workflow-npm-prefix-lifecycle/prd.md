# 工作流 npm 安装落点与 lifecycle 治理

## 目标

让 `pennix-component-lifecycle` 能明确管理工作流层全局 npm CLI 的用户级安装落点，并在发现系统级 npm 副本、重复入口、PATH 遮蔽或文件 owner 不符时给出可验证结果。目标用户 prefix 固定为 `$HOME/.local`，复用系统 Node.js/npm；AUR/Arch 包、项目本地依赖和 CCH 等 native owner 保持各自合同。

Paseo CLI 纳入唯一 catalog，但 Paseo 全套件、relay、Android、NAS、路由器、SSH 拓扑和凭据不属于本组件任务。

## 当前事实

- 生命周期当前只通过 `npm root --global` 观察一个 npm root，安装命令不携带固定 prefix，并在不可写 root 时自动加 `sudo`。
- 现有 catalog 登记 Trellis、FastCtx、CodeGraph 为 npm 包，但未声明用户 prefix；Paseo CLI 尚未登记。
- 现有迁移逻辑会在目标安装前清理 `replaces`，不满足“新路径安装并验证后再清理旧路径”的迁移顺序。

## 需求

- R1：npm catalog 组件声明用户 prefix、安装 owner 和必要的受控安装脚本；catalog 继续是版本、来源和动作的唯一来源。
- R2：`discover` 观察 `$HOME/.local`、系统 npm root、`/usr/local` 和既有用户 prefix，报告目标路径、实际命令路径、包名、版本和文件 owner。
- R3：`verify` 对目标 npm prefix、包 owner、命令 owner、版本和真实入口做阻断式核验。
- R4：npm 安装使用 catalog prefix 且用户 prefix 不调用 `sudo`；系统级旧副本只在目标安装和验收成功后精确清理。
- R5：补充 Paseo CLI 的官方 npm 固定版本 catalog 条目；其 daemon 重启和客户端重连由根任务按 Paseo 原生入口验收。
- R6：保留 AUR/Arch、项目本地 npm、native owner 和集合安装边界，不新增第二套版本表或通用安装 wrapper。
- R7：按用户明确修订，在现有用户级 npm `install`/`upgrade` 流程中通过原生 `npm config` 规范当前用户默认 prefix，复用 catalog 的目标值并回读验证；已匹配时不写入，失败时停止后续包安装及旧包清理，Skill 明确披露副作用。不新增组件、配置子命令、配置目标或收据，不修改其他 npm 键、系统或项目配置。

## 验收标准

- [ ] catalog 通过现有 schema 校验，所有目标 npm CLI 明确为 `$HOME/.local` 用户安装；Paseo 条目包含官方包、固定版本和受控脚本列表。
- [ ] lifecycle 测试覆盖多 prefix 发现、PATH 遮蔽、owner 漂移、用户 prefix 安装命令、系统旧副本延后清理和失败保留旧副本。
- [ ] 组件测试和离线 catalog/discover/verify 检查通过；不读取秘密、不写入真实运行态。
- [ ] 源仓库提交并推送，根任务记录精确提交；安装副本只通过原生 lifecycle 接纳，不直接编辑。
- [ ] 覆盖默认 prefix 修改/幂等、已匹配包仍执行配置核验、配置失败阻断安装和旧包清理、其他 npm 配置保留、非 npm/只读/卸载无配置写入；真实活动入口经原生接纳后验证，旧运行态不重装。
