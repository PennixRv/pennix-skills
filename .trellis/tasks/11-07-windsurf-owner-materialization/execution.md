# 实施进度

根已批准合同下，原生 plan advance、seal、approve、start 已完成，revision 1。生命周期导航已同步显式 reconcile、Windsurf owner 输入和 Paseo 仅自启边界；固定源与生成快照尚未修改。

前置 Windsurf v0.1.17 经维护者修正 Actions token 后，run 42355980168 attempt 3 的 npm publish 明确成功。CI 紧接的公开下载仍返回 404，整个 run 为 failure；待公开传播后，独立下载 SHA-256 与 attestation 的 471c397712aa90f94a42c31ba047850f1c06b8e08cfc76b9776d9f23c08ccb0a 完全一致，精确版本安装、npm audit signatures 的 registry signature 和 attestation 均通过。没有重复发布或移动 tag。

collection.json 固定 evidence E 50147de6a46bad1c02f2868915fbd77da8d3b061；沿既有 sync-collection 的精确 fetch、npm pack --ignore-scripts、完整生成路径物化，19 文件的集合、字节与 mode 全部匹配。生成后 verify（16 Skills/2 commands）、12 项集合测试、9 项评估和 diff 检查通过。源码发布的 124 项回归已通过；物化包不含 test 目录，包内 npm test 返回 0 tests，不能当作额外回归。8 个成员 Python 测试目录此前通过（1 项按原合同跳过）。

既有 Grok 固定源码与锁未变；原生 npm ci --omit=dev --ignore-scripts 成功，但 audit 报告其 undici 存在既有 high advisory（修复范围 <6.29.1）。本次不手改物化依赖或擅自升级 Grok，根侧记录独立基线风险，不把安装成功等同于无漏洞。
