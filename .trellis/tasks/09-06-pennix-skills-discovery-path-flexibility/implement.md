# 实施记录

- [x] 审计安装器、直接命令示例与跨 Skill 回退；确认安装器本来已接受合规替代根，但文档和
      `review-gate` 仍把 Codex 默认根写死。
- [x] 更新安装器帮助、README、受影响 Skill 示例与 `review-gate`；`PENNIX_SKILLS_ROOT`
      仅作调用方集合根约定。
- [x] 新增默认根、`.agents/skills` 目标和 `review-gate` 回退测试；补充长期质量规范。
- [x] 运行 8 组定向 Python 测试（44 个用例）、源集合 `--check` 和临时替代根的 12 Skill
      安装 smoke test。
- [x] 提交并推送实现提交 `9c81923`。
- [x] 从固定 checkout 重装当前默认用户集合，确认默认根为
      `/home/penn/.codex/skills/pennix-skills`、源与安装副本目录一致且共 12 个 Skill。
- [x] 修正替代根首次迁移示例的安装器路径，提交 `5c9f1c6` 并推送；随后再次校验并重装，
      当前默认根与源集合目录一致且共 12 个 Skill。
