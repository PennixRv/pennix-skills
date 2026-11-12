# 验证记录

## 集合候选

`python3 scripts/collection.py verify` 通过，保持 19 Skills、2 commands；治理 inspector／链接 5 项、路由合同 7 项、根 collection 合同 5 项全部通过。中文正文检查和 `git diff --check` 通过。静态完整性不代表实际模型会选择新版方法；按已批准合同不调用付费模型或其他执行者。

本次固定集合先交付方法变更；本项目 spec 现场迁移在原生新版 Trellis 安装后继续，源码任务收尾提交与运行集合固定提交分别记录。真实条目和历史仍待现场验收，不宣称当前任务完成。

公开集合 CI 43142243239 发现 project-update 的旧测试仍匹配前序命名调整前的整句，正文已使用当前机制名；保持正文合同，断言改为两个稳定机制标识，并补跑该 Skill 及公开 CI 的完整 Skill 测试。固定集合随修复提交重新核验，未发布旧失败候选。

最终固定集合 `95bf6ba9731560069eaf793b6542b3279f0a9064` 的公开 CI [43142738150](https://github.com/PennixRv/pennix-skills/actions/runs/43142738150) 成功。Lifecycle 0.2.56 固定该提交，公开载荷核验并安装后，通过原生 `pennix update pennix-skills --json` 和 `pennix repair pennix-skills --json` 更新、重装，均返回 changed。原生 status 为 match，集合 archive SHA256 `037c3b86864b078e768b302f3662c8be4a1df25027f31d08c5b68a3aa50a6297`。

本次后续证据提交不改变已部署集合成员内容；本项目的 spec 迁移仍依赖 Trellis beta.18 的公共发行和原生安装。保留现有真实规则与历史，未抢先删除旧占位。
