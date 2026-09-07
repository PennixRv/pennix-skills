# 旧用户级并行协议退役设计

`parallel-work`、`evidence-report`、`review-gate` 分别承担了现在应由 Trellis role/helper/Channel reference 和
coordinator task disposition 承担的职责。保留它们会让新项目遇到两份名称、结果 transport 和 sandbox 规则，因而
采用完整删除而非 wrapper/alias。

保留资产按职责划分：`trellis-research-record` 继续负责一切会产生 task research 的研究；
`pennix-workflow-routing` 只解释跨组件所有权和何时使用项目选择的 Trellis procedure，不持有 subnode schema；
installer 只部署直接 skill 根及其固定 submodule，不替代 Trellis init/update。

删除前用 Trellis release、marketplace workflow、root adoption 记录和 host receipt 确认替代路径存在。删除后以
git tag/commit 可回退旧 collection，但不保留同一 revision 中的双协议。
