# 退役网页搜索Skill并恢复原生路由

## Goal

实施根native-web-search-restoration已批准合同：移除Grok/Tavily网页搜索成员、命令与物化源，更新原生搜索路由及直接消费者，保留Windsurf等其余集合；验证并交付正式固定源。

## Requirements

- 删除两个退休网页搜索成员、grok-search命令及物化源，更新原生搜索／URL读取路由，保留Windsurf和其他17成员。
- 从真实源码修改，不手改已安装集合；通过集合及相关回归，提交推送供Lifecycle固定。

## Acceptance Criteria

- [ ] manifest精确为保留的17成员／1命令，源码树与声明一致，活动说明不再提供退休入口。
- [ ] collection verify、根及相关路由／合同回归通过；新集合被公开Lifecycle固定并通过双端安装、残留检查。

## Notes

需求与实施均已由根native-web-search-restoration完整合同及用户批准覆盖；根拥有整体双端及最终交付。本owner只完成列明源范围，不扩展外部服务或其他检索组件。
