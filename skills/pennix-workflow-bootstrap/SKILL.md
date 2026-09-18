---
name: pennix-workflow-bootstrap
description: Guided deployment entry for the Pennix Codex workflow. Use when the user explicitly asks to bootstrap, inspect, plan, apply, verify, or roll back workflow components; keep project actions plan-only unless separately approved.
metadata:
  short-description: Bootstrap the Pennix workflow safely
---

# Pennix Workflow Bootstrap

Use this Skill only for an explicit workflow deployment request. It is the
single user-facing deployment entry; component setup logic lives in its
internal adapters.

## 两类工作

Bootstrap 必须把系统安装和项目初始化分开显示、计划和确认。系统安装可以部署全局工具，
但不初始化任何特定项目；项目初始化必须携带明确的 `project root`，并单独确认。

### 系统安装

On a fresh Arch Linux host, before Codex or Pennix Skills exists, run:

```bash
bash "/path/to/pennix-skills/skills/pennix-workflow-bootstrap/scripts/seed-arch.sh"
```

The executable may be launched from either `bash` or `zsh`; its Bash shebang
selects the required interpreter. Execute it as a command rather than sourcing
it into the caller shell. The seed reads the adjacent `templates/` directory;
copy the whole `pennix-workflow-bootstrap` directory if relocating it.

It supports native Arch Linux and Arch Linux under WSL2. It installs the
current `openai-codex` candidate from the Arch official repository, prompts
for an OpenAI-compatible `base_url` and a hidden API key, renders the tracked
`templates/config.toml.seed` and `templates/auth.json.seed`, and materializes
the seed-owned fields in `CODEX_HOME/config.toml` and `CODEX_HOME/auth.json`.

The seed refuses to overwrite an existing `CODEX_HOME/config.toml` or
`CODEX_HOME/auth.json`. It does not clone or execute remote Pennix source,
write the key to TOML, print the key, or add the current package candidate to
the fixed component catalog. After a new Codex session starts, install Pennix
Skills, then let bootstrap plan the remaining system installation actions.

The supported host boundary is Arch Linux on Linux: native Arch Linux and
Arch Linux under WSL2. `pacman` handles official repository packages. For AUR
packages, prefer an already-installed `yay`, then fall back to `paru`.
Bootstrap does not install an AUR helper, guess package names, or force
independent/forked components through a package manager. Non-Arch hosts and
unknown/WSL1 environments are discoverable but all write actions are blocked.

After the seed, the system-installation actions are read-only `discover` →
read-only `plan` → explicit named actions with `apply --action <name> --yes` →
fresh `verify`. The plan marks these actions with `category=system-installation`:
Pennix Skills installation, installation-phase `config.toml` fields from
`templates/config.toml.install`, and the tracked `AGENTS.md.install` template.
The Skills source must be a clean, explicit Git checkout; the installer atomically
replaces only its managed `skills/pennix-skills` destination and rejects symbolic-link
paths or an unrelated file at that destination.
The config template is the portable static baseline only: it excludes host paths,
project trust, Web location, MCP/plugin state, marketplace state, hook hashes, and
user model, security, UI, or history preferences. Catalog package actions install
only a matching fixed candidate. Catalog plugin actions use Codex's native plugin
lifecycle only when the target marketplace is absent; an existing marketplace whose
ref cannot be verified is blocked rather than modified. If the subsequent plugin add
fails, bootstrap removes the marketplace it just created only when native inventory
proves no plugin was installed; any ambiguous state remains blocked for manual owner recovery.
FastCtx itself never materializes or refreshes user `AGENTS.md`; its normal Apply
and TUI paths leave that file untouched. The static Pennix template is the only
workflow-owned guidance source.

CCH and Tavily Hikari are catalogued for version discovery, but their endpoint/token
configuration remains under their native or external owners. A missing CCH installation
or Hikari CLI is therefore reported as a plan-only native-owner action, not installed
with guessed credentials or copied host configuration. OpenViking plugin installation
similarly verifies Codex plugin presence; remote server configuration and health remain
outside local bootstrap apply.

### 上游安装器与提问

对 catalog 含 `upstream_inspection` 的组件，planning gate 必须显式运行：

```bash
python3 "/path/to/pennix-skills/skills/pennix-workflow-bootstrap/scripts/bootstrap.py" \
  plan --inspect-upstream
```

该操作只读取 catalog 指定的 HTTPS 文本，限制大小、计算 SHA-256，并用组件专属 parser 检查已知的
安装控制面；它绝不执行下载内容。plan 将 inspection 的 URL、digest、状态和可适用性放进对应 action。
`upstream-contract-changed` 或 `unavailable` 会阻断该组件，不得以“继续执行上游脚本”绕过。

提问候选只来自 catalog 的 `decision_profile` 和 inspection 已知语义。已有工作流偏好、可唯一推导的
package manager、固定版本和不适用于选定交付方式的上游选项均自动记录而不提问。只有互斥答案会改变
范围、安全、成本、外部行为或验收，且每个答案都能映射到已审阅 adapter action 时才使用中文问题询问。
例如 AoE 的默认交付是 AUR package，故上游 `INSTALL_DIR` 不适用，不生成问题。

### 项目初始化

Trellis, CodeGraph, and AOE binaries may be installed by system actions, but
their project initialization is a separate `category=project-initialize` plan.
It requires `plan --project-root /absolute/project/path`; it may create `.trellis/`,
`codegraph.json`, indexes, or project workflow assets only after a separate
confirmation. It must never run as a side effect of the seed or Skills install.

During Trellis planning or an explicit `grill-me` gate, show the component key,
source/ref from the catalog, target, risk, precondition, postcondition, and
rollback receipt. Use Codex's native `request_user_input` directly when it is
present in the current session. Do not
probe for it through `functions.exec`, nested `tools.*`, `ALL_TOOLS`, shell, or
MCP. A schema error may be corrected and retried once; host refusal,
cancellation, timeout, or unavailable native interaction falls back to text and
stops the turn. Never auto-select the recommendation. Batch independent
decisions from the same gate when the host allows it; keep dependent decisions
separate. During implementation or apply, do not ask a new question: use the
sealed task/spec decision, or record `decision-needed` and return to planning if
the ambiguity is material.

For an upstream-inspected component, carry the SHA-256 emitted by the immediately reviewed plan into the named
apply action with `--upstream-inspection-digest <sha256>`. This is an explicit binding to the reviewed evidence;
`apply` does not retrieve or interpret upstream installer content.

All component versions and refs come from `references/component-versions.json`.
Do not add a second version table to this Skill or to an adapter. Do not print
secret values, full configuration, sessions, databases, logs, caches, locks, or
runtime state. `rollback` accepts only a receipt created by this bootstrap and
stops if the target hash has drifted.
