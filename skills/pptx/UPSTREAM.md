# 上游来源与本地维护

本项来自 [anthropics/skills](https://github.com/anthropics/skills/tree/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/pptx)，固定完整提交 `2c5958ecac7cee2b583967a2c4981d0f4a75c579`，对应子目录 `skills/pptx`。该提交将四项文档技能改为 Apache 2.0；原始 `LICENSE.txt` 完整保留。此目录由 pennix-skills 本地衍生维护，不属于 collection.json 的 materialized 项。

## 文件与差异

原始文件共 56 个，完整路径与原始 SHA-256 见 `upstream-files.sha256`。除下列本地适配外，上游文件保持原始字节；新增文件为本说明、摘要清单及适用第三方声明摘录。上游既有代码的修改标记见本节和脚本头部。

- `SKILL.md`：中文发现、默认只读、真实路径、受管 Python 与依赖缺失处理、临时目录及原件保护；保留原创建编辑方法，仅在明确写入请求时使用。
- `scripts/office/soffice.py`：移除 AF_UNIX 检测、C shim 编译和 LD_PRELOAD 注入；保留临时 profile，并在新 profile 禁止不受信宏。环境限制仍生效。

上游根 `THIRD_PARTY_NOTICES.md` 已逐类检查：四个目录不含字体、imageio、imageio-ffmpeg 或 FFmpeg 发行资产；这些资产未随本集合复制。PDF/PPTX 脚本使用 Pillow 时依赖由独立运行时发行，相关上游 HPND 声明保留在其目录。OOXML schema 保留原始文件及现有头部，没有增加其他来源文件。系统软件及运行时包的许可随其原生发行保留，不将 Apache 2.0 扩展到这些依赖。

## 升级和核验

用 `gh api repos/anthropics/skills/tarball/<完整提交>` 取得固定归档，只提取本项子目录到新的临时目录。先核验完整文件集合和摘要，再用 `git diff --no-index -- <原始子目录> <本地目录>` 审阅新增、删除和字节差异；本地新增说明文件会显示为新增。按原生 apply_patch 重新审阅适配，不覆盖安装副本，不用可变 HEAD 作为固定来源。升级时同步本说明、摘要清单和许可检查，运行集合及文档技能检查；依赖安装仍由 Lifecycle 管理。
