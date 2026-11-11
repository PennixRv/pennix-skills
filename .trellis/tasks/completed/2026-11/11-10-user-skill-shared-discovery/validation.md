# 用户 Skill 共享发现实施验收

本组件运行内容已提交并推送，Lifecycle 固定及实际安装来源为 `e8b5982d4b3ab99e37dee83b74fad9c3ed514394`。集合仍含 15 Skills 和 2 commands，未新增 Skill、独立注册表或执行器。用户授权、根合同与组件 seal/approve/start 均已生效；由当前会话完成源码实施，没有实现子代理。

确定性验证：既有 evaluation 单元测试 15 项、routing 合同 5 项、collection verify 均通过。来源验证区分 CODEX_HOME 的配置与 HOME 的共享实体，核验实际 receipt.target、固定提交、manifest 与树摘要。行为观察保留首次失败及顺序，不以后续读取成功覆盖。

根侧已经完成 Lifecycle `0.2.46`、Context Mode `2.1.5-pennix.4` 正式发布安装与共享配置迁移。默认原生发现 63 项无重复或错误；主 15、extra 10、Context Mode 三命令均为共享实体，空 CODEX_HOME 不复制配置与认证也能发现这些实体。项目、system 与插件保留声明位置。根离线组合门禁 11/11、自测通过。

真实 Codex `0.167.0` / OpenAI / `gpt-6.1-sol` / xhigh 完成 app-server 新会话、独立进程 resume、原生 compact 后读取和独立 CLI 四场景。每组完整读取主、extra、项目、Context Mode、system 和插件六项目标及 routing 相对参考，无首次失败或错误路径；是当前样本证据，不承诺未来零误读。原始 trace 与运行态不提交 Git。

根侧完整提交、发行摘要、迁移身份和限制见 `11-09-user-skill-placement-governance/validation.md`。Context Mode 原生 doctor 的受管 env 诊断差异已由旧正式 `.1` 复现并单独记录问题，不属于本组件改动或本轮新增回归。未实测其他操作系统、其他真实宿主，不卸载生产共享集合。当前任务无后台写入者和委派资源，按组件原生 archive 收尾；归档只改变文档，不改变已安装的固定运行内容。
