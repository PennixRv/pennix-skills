# pennix-skills

用户自维护的 Codex 工作流 Skills 源码。

通用 Trellis Skill 随 Trellis 组件交付；本仓库只维护用户工作流策略、确定性辅助脚本和
对应测试。`skills/fast-context` 是独立 `fast-context-skill` 组件的 Git submodule：该组件
继续拥有 CLI、测试和 npm 发布，本仓库只固定其在私有 Skills 组合中的版本。

首次引导可使用 Codex 官方 `skill-installer` 安装不依赖子模块的安装 Skill：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo PennixRv/pennix-skills --path skills/pennix-skills-install \
  --dest "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills"
```

随后从明确的本地 checkout 安装或更新完整组合：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/pennix-skills-install/scripts/install.py" \
  --source "/path/to/pennix-skills"
```

该命令只在显式安装请求时运行。它初始化 checkout 已固定的 submodule，并将每个直接
`skills/<name>/` 物化到 `${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/<name>/`。它不新建
源码 checkout、不切换分支、不选择版本，也不更新已固定的组件版本；若本地缺少对象，初始化
submodule 只会取得当前 Gitlink 固定的提交。安装副本不是源码编辑位置，也不生成第二份版本或
状态事实。
