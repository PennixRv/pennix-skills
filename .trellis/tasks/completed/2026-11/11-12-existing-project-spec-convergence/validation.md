# 验证记录

## 集合候选

`python3 scripts/collection.py verify` 通过，保持 19 Skills、2 commands；治理 inspector／链接 5 项、路由合同 7 项、根 collection 合同 5 项全部通过。中文正文检查和 `git diff --check` 通过。静态完整性不代表实际模型会选择新版方法；按已批准合同不调用付费模型或其他执行者。

本次固定集合先交付方法变更；本项目 spec 现场迁移在原生新版 Trellis 安装后继续，源码任务收尾提交与运行集合固定提交分别记录。真实条目和历史仍待现场验收，不宣称当前任务完成。

公开集合 CI 43142243239 发现 project-update 的旧测试仍匹配前序命名调整前的整句，正文已使用当前机制名；保持正文合同，断言改为两个稳定机制标识，并补跑该 Skill 及公开 CI 的完整 Skill 测试。固定集合随修复提交重新核验，未发布旧失败候选。

最终固定集合 `95bf6ba9731560069eaf793b6542b3279f0a9064` 的公开 CI [43142738150](https://github.com/PennixRv/pennix-skills/actions/runs/43142738150) 成功。Lifecycle 0.2.56 固定该提交，公开载荷核验并安装后，通过原生 `pennix update pennix-skills --json` 和 `pennix repair pennix-skills --json` 更新、重装，均返回 changed。原生 status 为 match，集合 archive SHA256 `037c3b86864b078e768b302f3662c8be4a1df25027f31d08c5b68a3aa50a6297`。

本次后续证据提交不改变已部署集合成员内容；本项目的 spec 迁移仍依赖 Trellis beta.18 的公共发行和原生安装。保留现有真实规则与历史，未抢先删除旧占位。

## 现场迁移与最终验收

前述发行依赖现已解除。Trellis beta.18 发布运行 `43146526460` 第二次成功，公共包核验及 Lifecycle 原生安装、重装完成。本项目使用已安装 CLI 原生 `update --skip-all` 更新四个方法、版本及模板元数据；普通 `init --yes` 补齐缺失总索引，再由本会话维护实际导航。

删除三份纯占位 backend 文件和七份 frontend 文件；准确路径保留于本次 Git diff，可从迁移前提交 `8a3aff5dc32eb0d667ffe541783c93164225373a` 同路径恢复。quality/logging 保留实际主体和原路径，仅删除占位段；主体 SHA256 分别为 `565073d44333447beee9be908726ad97c1b575e1ae90b24fffaa438a5cbe973a`、`5b096e08e765e48b660d73697dac078ec78c0bafaf084e905bfbb0c337b6f5bc`。backend 索引改为集合质量与评估证据导航，不增加领域模板。共享 guides 保留历史案例，只修正当前检查语句与入口说明。

最终七份规范无占位、无失效本地导航；两个 native session-start 均发现总索引，packages 返回 backend。重复 init 的 spec、任务、配置摘要完全一致，无 frontend 复建；最终 update dry-run 已是最新。AGENTS、workflow、项目配置、既有归档均未改变，无 `.new` 候选遗留。四个更新方法与公开发行构建逐字一致，原生备份保留。

已安装集合仍固定 `95bf6ba9731560069eaf793b6542b3279f0a9064` 且 status match；这些项目资产、规范和任务记录不改变集合成员，不需要另发集合版本。不调用付费模型、Copilot 或其他执行者；静态／原生消费证据不代表模型自主选择证明。
