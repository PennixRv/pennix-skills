# 方案

实际修改 SiYuan/Hikari 的 `scripts/connection.py`、Grok 的 `scripts/lib/lifecycle.js` 及对应原生测试。只读预检提取自已有 configure 前置，执行仍复查；protocol_version=1，operation_id 绑定结果，effect 不能由字符串猜测。Grok 按现有字段、受支持别名及 receipt 判断外部/归属，缺少部分字段不能授权覆盖。

Windsurf 从独立仓库正式验收并发布的固定运行包刷新，由 collection.json/sources 维护来源，不复制 Lifecycle 执行器。保留中央秘密/Devin 数据边界。主会话按组件约定实施，不创建写 worker；不修改其他 Skill 的无关内容。接口与根合同一致，无新增重要取舍。
