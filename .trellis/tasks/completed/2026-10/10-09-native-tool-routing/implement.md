# 执行计划

1. 完成真假判断和 owner 归属，关联 pennix-skills 的 10-09-native-tool-routing。
2. 根任务原生 seal/approve/start；approve basis 如实记载本轮“无额外审批”委托。
3. 组件 task 完成同等资产后原生激活；用 apply_patch 修改源码 Skill 和 AGENTS 模板，更新模板 catalog 摘要。
4. 运行既有路由、集合/静态部署测试和 quick_validate；审查差异。提交推送 GitHub main，以明确提交作为 Skills 发布版本。
5. 系统 skill-installer 按唯一 catalog paths/ref 安装至同级 staging，旧 lifecycle 精确卸载旧 AGENTS 受管块；新 lifecycle replace-staged 并安装新块。核验 digest、receipt、块外内容和集合，清理本轮 staging/临时文件。
6. 根侧记录真实性、发布、安装和限制；更新关联版本记录。组件 task 与两个根任务归档、journal、全量提交，root 保持 main。

回滚：未替换前保留旧安装；staging 或 receipt 验证失败停止。若受管替换后验证失败，从已发布上一提交按同一 installer/lifecycle 协议重装旧集合和匹配块，绝不手改 receipt/pointer。仅清理本轮已确认所有的临时资产。

