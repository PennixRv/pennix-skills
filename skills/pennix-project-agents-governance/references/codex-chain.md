# Codex 指令来源链

依据：[OpenAI 官方 AGENTS 指南](https://developers.openai.com/codex/guides/agents-md)，2026-10-14 核验。用户层优先非空 `AGENTS.override.md`，其次 `AGENTS.md`；项目根到 cwd 每层按 override、AGENTS、配置 fallback 顺序最多选一个非空文件。没有项目根时仅检查 cwd。更近目录细化前层规则；默认文档字节上限为 32 KiB。

本 Skill 的 `scripts/inspect_chain.py` 只读输出路径、字节量、遮蔽来源与潜在截断，不输出正文，不仿造宿主加载回执。先确认宿主根目录及实际有效 `project_doc_fallback_filenames`、`project_doc_max_bytes`；配置层/profile/CLI 覆盖或不可见宿主状态无法核验时保持 `configuration=unknown`。

```bash
python3 <skill>/scripts/inspect_chain.py --project-root /absolute/project \
  --cwd /absolute/project/subdir --codex-home /absolute/codex-home \
  --max-bytes 32768 --config-confirmed
```

有 fallback 时按实际顺序重复 `--fallback NAME`。没有可确认项目根时省略 `--project-root`，只检查 cwd；不要猜测父目录或穿越独立 submodule。路径/读取失败给 `unknown`，符号链接只读解析并报告，不能据其可读性授权原生 writer。helper 的 raw-byte budget 是截断候选，宿主附加标签或不同预算口径可能更早截断；实际主会话/节点加载仍需原生使用证据，静态 `candidate` 不能冒充 `loaded`。
