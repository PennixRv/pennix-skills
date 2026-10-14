# 设计

两个 Skill 分别负责项目文件治理和 CodeGraph 配置/使用导航；系统部署交 lifecycle，项目块交 CodeGraph/Trellis 原生 writer，原生 MCP/CLI 文档为唯一协议权威。

治理流程为 inspect → plan → apply 手工正文或 delegate 生成块 → verify。沿当前有效来源链审阅内容，不将文件与其内部块并列。结果回写当前 task/Issue/spec，不创建全局重复台账。

复用 lifecycle collection、npm 安装和状态探针；迁移只对精确已核验 AUR 包/版本/owner 提供有界路径。只读 helper 使用标准库，配置不确定和截断明确报告，不伪装为宿主运行态。
