# 组件交付记录

## 产品提交

- 产品代码与组件测试对应的精确提交为 `2d54c91802fa69d95436eb7bbaaf3d459c1e8140`（`fix: tighten session handoff intake contract`）。
- 该提交已推送到 `pennix-skills` 的 `origin/main`；根仓库固定此产品提交，不把后续仅含任务证据的提交误当作安装内容版本。
- 当前变更不需要 npm 发布、版本标签或其他公开发布；安装器从 Git 提交读取组件集合。

## 原生安装与替换

安装使用系统原生 installer，以产品提交为 ref，并完全采用 catalog 中的 12 个 Skill 路径：

```text
python3 /home/penn/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo PennixRv/pennix-skills \
  --ref 2d54c91802fa69d95436eb7bbaaf3d459c1e8140 \
  --method git \
  --path <catalog 中的 12 个路径> \
  --dest /home/penn/.codex/skills/pennix-skills.staging-20261010T042500Z
```

预替换检查结果：12 个 Skill、141 个源文件与产品提交一致，文件内容和执行权限一致，`quick_validate.py` 通过。随后通过组件原生生命周期入口执行 `replace-staged --component pennix-skills --yes`，结果为 `status: changed`；staging 目录已被消费。

替换后检查结果：

- `verify --component pennix-skills` 返回 `status: match`，`failures` 与 `advisories` 均为空。
- `discover --component pennix-skills` 返回集合匹配且无 staging 残留。
- `/home/penn/.codex/skills/pennix-skills` 中源提交的 141 个文件逐文件内容和模式匹配。Grok catalog 的安装后步骤生成 `grok-search/node_modules/` 下 177 个运行时文件，属于安装合同中的生成目录，未计入源文件差异。
- 已安装副本的 `pennix-session-handoff` 两个测试模块共 33 项通过。

## 根侧落点

根仓库的 acceptance 固定产品提交 `2d54c91802fa69d95436eb7bbaaf3d459c1e8140`，并记录离线集成验收、安装验证和原始交接样本 SHA 未变化。根仓库没有远程，根侧只提交协调记录，不复制组件源码或安装运行态。
