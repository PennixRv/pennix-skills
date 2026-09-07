# 实施计划

1. 读取具体 Skill、installer、README、tests 和路由引用，建立精确删除清单；确认 Trellis release、marketplace pin
   与 root host/adoption evidence 已完成。
2. 删除旧三个 Skill 全部受控文件并更新 indexes/routes/docs；不修改无关 Skill 或 fast-context Gitlink。
3. 更新/新增安装器和路由测试，执行 direct Skill validator、installer `--check`、临时 destination install 和 repo
   test suite。
4. 检查无遗留术语或旧 runtime 所有权，记录 release compatibility；提交、推送并由官方 installer 重装集合。
