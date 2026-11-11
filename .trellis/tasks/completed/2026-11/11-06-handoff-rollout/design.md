# 交接精确定位设计

复用根任务已批准的 design.md：现有 handoff.py 增加 resolve-rollout，标准库 SQLite 以 mode=ro 打开 `${CODEX_HOME:-$HOME/.codex}/state_5.sqlite`，参数化查询精确线程 ID，只返回唯一匹配路径；验证普通绝对文件及首条 session_meta.payload.id。回执复用 emit/ContractError，不读取消息正文，不扫描会话，结构错误受控失败。Skill 在请求准备前使用该回执；旧 path 合同与包 schema 不变。

修改边界：handoff.py 提供命令；独立 test_resolve_rollout.py 覆盖真实 CLI 与临时 fixture；SKILL.md 指导调用；backend quality-guidelines.md 固化复发预防。无需修改 collection.json、Trellis、Hook、全局配置或安装副本。主会话实施/检查，当前宿主未提供可调用子代理入口。

本机已验证 Codex 0.166.0 的 state_5.sqlite；不能据此承诺未来数据库结构稳定。数据库、线程或文件身份不符即停，不用扫描后备。源码 main 起点 f7cbfe92cb678026e4af4d46b197cf757064d62a，与远端 main 一致。

测试通过后提交推送 main，Git commit 即集合新版本；根任务由 pennix update pennix-skills 安装，核对锁与 receipt，固定 gitlink 并运行组合验收。不引入 semver 发布体系。回滚用新的 Git revert 提交及原生安装事务，不手改安装树、凭据或回执。
