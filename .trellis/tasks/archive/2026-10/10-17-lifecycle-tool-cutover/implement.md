# 实施计划

1. 用新 Skill 正文替换旧生命周期操作说明，保留组件 owner 和项目初始化边界。
2. 删除旧 lifecycle 脚本、适配器、seed、catalog、模板和只服务旧机制的测试/fixture。
3. 搜索活动源码和文档中的旧命令与旧路径，修复遗漏引用；不修改归档历史。
4. 运行仓库测试、Markdown/链接检查和 `git diff --check`，确认集合固定提交与工具 catalog 的来源关系由工具仓库维护。
