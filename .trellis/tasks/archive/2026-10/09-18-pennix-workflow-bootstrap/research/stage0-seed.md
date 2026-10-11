# Stage 0 Seed 研究与合同

## 外部依据

- [OpenAI Codex CLI features](https://developers.openai.com/codex/cli/features) 当前官方页面给出
  Linux/macOS standalone installer，并说明 Codex 的安装/更新入口。
- [OpenAI Authentication](https://developers.openai.com/codex/auth) 说明 Codex 使用
  `CODEX_HOME/auth.json`（默认 `~/.codex/auth.json`）或系统 credential store 缓存登录凭据；
  本项目选择直接渲染提取的 `auth.json.seed` 模板，以保持基础文件由 Pennix 静态模板控制。
- [OpenAI Configuration Reference](https://developers.openai.com/codex/config-reference) 定义了
  `model_provider`、`model_providers.<id>.base_url`、`wire_api` 和 `requires_openai_auth`；
  自定义 provider 使用 OpenAI authentication 时设置 `requires_openai_auth = true`，不使用
  `env_key`，provider 配置属于用户级 `~/.codex/config.toml`。
- 当前实机 `codex features --help` 提供 feature 管理命令，`codex features list` 显示
  `default_mode_request_user_input`；Stage 0 将该字段直接从 `config.toml.seed` 模板物化，
  不调用原生 CLI 改写基础配置。
- 当前实机 `pacman -Si openai-codex` 返回 Arch `extra` 官方包，Stage 0 使用 `pacman -Syu --needed`
  保持 Arch 滚动发行版的完整升级语义；候选版本只用于启动输出，不写入固定 catalog。

## Stage 0 合同

1. 只接受 native Arch 或明确 WSL2 的 Arch；其他环境立即停止。
2. 必须检测 `openai-codex` 官方候选包；候选缺失时不猜测 AUR 包、不远程执行其他安装脚本。
3. 只在 `CODEX_HOME/config.toml` 和 `CODEX_HOME/auth.json` 都不存在时读取并渲染 seed 模板；
   任一已存在即失败关闭。
4. API key 只进入 `auth.json.seed` 的替换结果，并以 `0600` 写入 `auth.json`；stdout、stderr、
   任务、receipt、Git 和 TOML 都不能包含 key。
5. seed 完成后输出短提示词，指导用户启动新 Codex session，安装 Pennix Skills；installation
   再物化 install config 与 `AGENTS.md` 模板，最后使用 `pennix-workflow-bootstrap` 开始部署。

## 与 Stage 1 的边界

Stage 0 的 current candidate 是“让 Codex 能启动”的一次性 seed，不是版本治理。后续
`pennix-workflow-bootstrap` 才负责 install 模板、静态 catalog、完整组件 discover/plan/apply/verify/rollback、
项目边界和 receipt。两阶段之间必须经过新 Codex session，不能假定当前会话自动刷新工具清单或
Skills。
