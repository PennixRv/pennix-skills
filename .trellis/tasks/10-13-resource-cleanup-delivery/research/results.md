# 清理指导交付

新增 `pennix-resource-cleanup`，配套资源策略与结果合同覆盖批准范围的组件；routing 和唯一 catalog 注册该入口。默认只读盘点与预览，复用已有明确执行授权，不扩大 owner 或目标范围。没有原生入口、活动保护或部署证据不足时保留资源；不新增全局清理器。

Grok 物化文件通过其已提交树的 `git archive` 导出，来源为 `ce76b2a78e9fb416eff0b7edb6de6db75c94ffda`；不复制工作树未提交任务、凭据、缓存或运行态。catalog 固定 Trellis beta49 和 FastCtx 0.2.25。

首批生命周期 176 tests 通过；补齐后再次核验引用/frontmatter、完整 unittest、物化 Grok 离线测试与公开 replace-staged / verify。安装和最终 SHA 的实际证据由根任务记录。

此前误写活动安装树并尝试私有 receipt writer，已撤销；从旧来源 `ed09d88` 隔离重建核验旧摘要后恢复原树，公开 replace-staged 成功。最终接纳再次使用原生 system installer 暂存，不直接覆盖活动目录或改收据。
