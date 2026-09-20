# 技术设计：远程 seed 入口

## 组件边界

只修改 `pennix-workflow-lifecycle` 的 seed 脚本、测试和用户文档。生命周期 catalog、正式
package/plugin adapters、项目初始化边界不改变。

## 运行模式

```text
local checkout
  seed-arch.sh -> adjacent templates/

curl | bash
  raw seed-arch.sh -> raw static template files -> temp dir
                     -> /dev/tty prompts
                     -> config.toml + auth.json
```

脚本通过模板可用性和执行来源判断模式；不复制模板内容到第二份 shell here-doc。remote mode
的 HTTP 结果只作为模板输入，不通过 `eval`、`source` 或子 shell 执行。

## 安全与幂等

- 固定 HTTPS raw base，只请求 `config.toml.seed` 和 `auth.json.seed`。
- `curl` 失败、空响应、模板缺失或模板路径异常立即失败。
- remote mode 在 `/dev/tty` 不可读时立即失败；不能将脚本 stdin 当作答案。
- 继续使用现有 `CODEX_HOME` symlink gate、existing-file refusal、atomic temp write、`0600` 和 cleanup。
- 新环境第一次成功；第二次看到已有 config/auth 并在 package 安装前失败，保持现有保护合同。

## 文档合同

README 和 lifecycle Skill 只重复入口用法、阶段边界和操作语义，不重复任何 approved component version。
seed 完成后的提示只指导安装 Pennix Skills 和进入 lifecycle，不声称组件 profile 已安装。
