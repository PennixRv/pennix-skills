---
name: pennix-workflow-lifecycle
description: Guided lifecycle entry for the Pennix Codex workflow. Use when the user explicitly asks to inspect, install, upgrade, uninstall, or verify workflow components.
metadata:
  short-description: Manage the Pennix workflow lifecycle safely
---

# Pennix Workflow Lifecycle

Use this Skill only for an explicit workflow deployment request. It is the
single user-facing deployment entry; component setup logic lives in its
internal adapters.

Lifecycle manages configuration intent and readiness, not a shared secret
store. The catalog declares the finite configuration targets, and a local
private profile records only which optional targets the operator selected.
Secret values stay in a private owner record or an owner-controlled terminal
flow. Do not create a shared `.env`, place a value in chat, task artifacts,
arguments, environment variables, or inventory output, or copy one component's
credential into another component's configuration.

## 两类工作

Lifecycle 必须把系统安装和项目初始化分开显示、计划和确认。系统安装可以部署全局工具，
但不初始化任何特定项目；项目初始化必须携带明确的 `project root`，并单独确认。

### 系统安装

On a fresh Arch Linux host, before Codex or Pennix Skills exists, prefer the
remote seed entry:

```bash
curl -fsSL https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/scripts/seed-arch.sh | bash
```

When either seed file is missing, the remote entry fetches the two static
templates over HTTPS and reads the needed answers from `/dev/tty`; it fails
before package/config writes when no control terminal is available. It needs
neither templates nor a terminal when both files already exist. When no AUR
helper exists, it also checks out and builds the `yay` AUR package. It does not
clone or execute the Pennix source.

For maintenance and offline fixture testing, the executable may be launched
from either `bash` or `zsh`; its Bash shebang selects the required interpreter.
Execute it as a command rather than sourcing it into the caller shell. The local
seed reads the adjacent `templates/` directory; copy the whole
`pennix-workflow-lifecycle` directory if relocating it.

It supports native Arch Linux and Arch Linux under WSL2. It installs `npm` from
the official repository and the current `openai-codex-bin` candidate from AUR,
prompts only for a missing
OpenAI-compatible `base_url` or hidden API key, renders the tracked
`templates/config.toml.seed` and `templates/auth.json.seed`, and materializes
only missing seed-owned files in `CODEX_HOME`. Existing files are preserved
exactly, so the seed is reentrant without prompting when both already exist.
If the catalog-authorized legacy `openai-codex` package is installed, the seed
migrates it through the selected AUR helper to `openai-codex-bin`; it does not
guess or remove an unlisted package owner.

The seed does not clone or execute remote Pennix source, write the key to TOML,
print the key, or add the current package candidate to the fixed component
catalog. It accepts no arguments: `seed-arch.sh --uninstall` is rejected before
any write.

Its completion output uses the current Codex session's next user turn, not a
new session. The first turn installs only the catalog's `bootstrap_skill` with
the system `$skill-installer`. The installer reports that a newly installed
Skill is available on the next turn; the next turn stays in the same session
and invokes this Skill.

In that next turn, run read-only `discover` first. If `pennix-skills` is
`bootstrap` or `partial`, read `missing_skills` and the single
`collection_contract` from `references/component-versions.json`. For a complete
install or upgrade, install all catalog paths into a new sibling staging
directory under `$CODEX_HOME/skills` using `$skill-installer`; do not install
into the live collection and do not create a repository checkout. The catalog
collection source paths are the only input to those installer calls; materialized
entries provide provenance and closed post-install metadata. Verify that the
staged tree contains exactly the catalog Skill names and valid frontmatter, then
run:

```bash
python3 <installed-lifecycle>/scripts/lifecycle.py replace-staged \
  --component pennix-skills --staging "$CODEX_HOME/skills/.pennix-skills-stage" \
  --destination "$CODEX_HOME/skills/pennix-skills" --yes
```

`replace-staged` runs only catalog-defined post-install action IDs, creates a
private integrity receipt for the final tree, and refuses unknown or drifted
live content. An explicit, confirmed `replace-staged --yes` may migrate an
exact legacy collection that has no receipt; this is the one-time receipt
bootstrap and is still transactional. Automatic refresh and `uninstall` refuse
legacy or drifted full collections. The command leaves live content in place
when staging validation, preparation, or replacement fails. A missing or
partial catalog-only collection is reentrant. A user-created entry is never
deleted. Rerun `discover` and `verify` after replacement. Do not retype a
parallel Skill list in prompts or documentation.

The collection receipt excludes Python's regenerable `__pycache__` directories
and `.pyc` files from its digest. These files are runtime cache, not managed
Skill content; all other files, modes, directories and symlink checks remain
part of the integrity contract.

The supported host boundary is Arch Linux on Linux: native Arch Linux and
Arch Linux under WSL2. Lifecycle package actions prefer an already-installed
`yay`, then `paru`, and finally `pacman`. Stage 0 Codex installation follows
the same AUR path: when neither helper exists, it installs `base-devel` and
`git` through `pacman`, then builds `yay` from its AUR package before installing
`openai-codex-bin`. Lifecycle itself does not install an AUR helper, guess
package names, or force independent/forked components through a package manager.
Non-Arch hosts and unknown/WSL1 environments are discoverable but all write
actions are blocked.

After the seed, the system-installation lifecycle is direct and component-scoped:
`discover` → `install|configure|upgrade|uninstall --component <name> --yes` → fresh
`verify`. `discover` is read-only and reports the catalog target, observed
version, actual package owner, and repository candidate; it never writes the
catalog or applies a candidate.
`verify --component <name> --yes` validates only that catalog component, its
component-specific integrity and upstream contract. An unknown component is an
error and never falls back to full verification. `verify --yes` is the full
workflow baseline and also checks core and enabled configuration targets. Both
forms return a structured `verification` object with `scope`,
`checked_components`, `failures`, and `advisories`; only `failures` produce a
blocking status and exit code. For a `repository-latest` package, a readable
installed version behind a readable repository candidate is an
`upgrade-available` advisory. Missing, unknown, unsafe-owner, pinned-drift,
static-drift, and required-readiness states remain blocking.
`pennix-skills` is an installed collection, not a static component: its
install and upgrade actions belong to the system `$skill-installer`; lifecycle
discovers the catalog's exact entry set, receipt state, and only uninstalls an
exact receipt-matched collection. `bootstrap` is an exact single-Skill initial
shape; `partial` is a safe, catalog-named subset with valid frontmatter and an
explicit `missing_skills` list. Both resume through the same-session procedure
above; unrelated entries, invalid frontmatter, legacy complete collections, and
unknown content remain blocked and are never repaired or removed automatically.
`codex-config`, `codex-agents`, and `tmux-config` are the supported static
components. Static assets are independent from sensitive configuration targets:
they use tracked templates, managed blocks, per-asset integrity receipts, and
fail-closed drift handling; they never read or write the private configuration
profile or a shared `.env`. `codex-config` accepts an existing configuration as
`compatible` when all lifecycle-owned values are semantically present, and leaves
additional user-owned values untouched. `codex-agents` manages only its two lifecycle marker
blocks and preserves all unowned `AGENTS.md` content; missing owned blocks may be
added, while duplicate, unpaired, or modified owned blocks block the operation.
`tmux-config` is an explicit component action and manages only the Pennix block in
`HOME/.tmux.conf`. Its baseline covers
`default-terminal`, true-color `terminal-overrides`, and the paired tmux window
foreground/background styles. It does not manage the CCH block, CCH runtime
files, status-bar layout, shell startup, user shortcuts, or project assets.
Install and collection replacement do not implicitly write this block. Use
`discover` and `verify` to see the static asset state separately from package
installation and configuration readiness. Catalog keys address package and
plugin components separately.
The config template is the portable static baseline only: it excludes host paths,
project trust, Web location, MCP/plugin state, marketplace state, hook hashes, and
user model, security, UI, or history preferences. Catalog package actions install
only a matching fixed candidate, except `codex-cli`, which follows its current
AUR repository candidate. A catalog `replaces` entry is the complete
allow-list for a known package-owner migration (for example the unscoped
`fastctx` npm package to `@pennixrv/fastctx`); the old owner is removed through
the same native package manager before installation. An unlisted or
unverifiable command owner blocks the operation and is never deleted
automatically. Catalog plugin actions use Codex's native plugin
lifecycle when the target marketplace is absent or Codex reports a native marketplace
root whose Git `HEAD` exactly resolves to the catalog ref; an existing marketplace whose
ref cannot be verified is blocked rather than modified. If the subsequent plugin add
fails, lifecycle removes the marketplace it just created only when native inventory
proves no plugin was installed; any ambiguous state remains blocked for manual owner recovery.
FastCtx itself never materializes or refreshes user `AGENTS.md`; its normal Apply
and TUI paths leave that file untouched. The static Pennix template is the only
workflow-owned guidance source.

### 配置目标

After the relevant delivery component is `match`, use the explicit target ID:

```bash
python3 <installed-lifecycle>/scripts/lifecycle.py configure \
  --component <target-id> --yes
```

`discover` reports every catalog target's redacted readiness state and whether
it is enabled. `codex-provider` is the only core target. It delegates to the
native `codex login` terminal flow, which OpenAI's official documentation names
as the default browser sign-in path. Each optional target becomes enabled only
after an explicit configure attempt, so a later `verify` checks the selected
integration without requiring unrelated services on every host.

The catalog currently defines `openviking-connection`, `cch-connection`,
`hikari-connection`, `grok-search-provider`, `grok-tavily-extra`,
`grok-firecrawl-extra`, and `windsurf-credential`. CCH and Windsurf delegate
to their owner `configure` command. Hikari and Grok accept values only through
`/dev/tty`, conceal secret input, and write a private owner record. Grok refuses
to overwrite a non-lifecycle-marked record. OpenViking has no local owner setup
adapter yet; selecting it reports a blocked result instead of guessing remote
server configuration. A target's delivery must match first, and collection
targets additionally require a matching collection receipt.

The profile is stored below `CODEX_HOME` with mode `0600`, contains target IDs
and a normalized configuration-contract digest only, and is safe to recreate.
Ordinary component version updates preserve it. If the configuration contract
changes, `discover` marks it `stale`; rerun the relevant explicit configure
action to reseal it. `verify` requires the core target and every enabled optional
target to be ready or configured, while never printing a secret, its path, or a
configuration value.

### 上游安装器与提问

对 catalog 含 `upstream_inspection` 的组件，`install` 和 `upgrade` 会在调用原生 owner
前读取 catalog 指定的 HTTPS 文本，限制大小、计算 SHA-256，并用组件专属 parser 检查已知的
安装控制面；它绝不执行下载内容。`upstream-contract-changed` 或 `unavailable` 会阻断该组件，
不得以“继续执行上游脚本”绕过。

提问候选只来自 catalog 的 `decision_profile` 和 inspection 已知语义。已有工作流偏好、可唯一推导的
package manager、固定版本和不适用于选定交付方式的上游选项均自动记录而不提问。只有互斥答案会改变
范围、安全、成本、外部行为或验收，且每个答案都能映射到已审阅 adapter action 时才使用中文问题询问。
例如 AoE 的默认交付是 AUR package，故上游 `INSTALL_DIR` 不适用，不生成问题。

### 项目初始化

Trellis, CodeGraph, and AOE binaries may be installed or upgraded by their
catalog component key, but project initialization remains a separate native
operation. Lifecycle never creates `.trellis/`, `codegraph.json`, indexes, or
project workflow assets as a side effect of a system lifecycle command.

Before a direct lifecycle command, show the component key, source/ref from the
catalog, target, risk, and expected owner operation. Use Codex's native `request_user_input` directly when it is
present in the current session. Do not
probe for it through `functions.exec`, nested `tools.*`, `ALL_TOOLS`, shell, or
MCP. A schema error may be corrected and retried once; host refusal,
cancellation, timeout, or unavailable native interaction falls back to text and
stops the turn. If answers arrive in the same native continuation, persist the
decision, re-evaluate dependent gates, and continue the current lifecycle flow;
do not close the turn merely because a question was asked. Never auto-select the
recommendation. Batch independent decisions from the same gate when the host
allows it; keep dependent decisions separate. During implementation, do not ask
a new question: use the sealed task/spec decision, or record `decision-needed`
if the ambiguity is material.

All component versions, refs, configuration targets, and closed post-install
action IDs come from `references/component-versions.json`.
Do not add a second version table to this Skill or to an adapter. Do not print
secret values, full configuration, sessions, databases, logs, caches, locks, or
runtime state. `uninstall` only removes exact lifecycle-owned files, an exact
Pennix Skills collection, or a package/plugin through its native owner; drifted
content is left untouched. Stage 0 has no uninstall mode and never removes
`auth.json`, its Codex package, AUR helpers, build dependencies, full Skills,
plugins, or project assets. After the collection is present, remove one explicit
lifecycle component at a time; revoke or rotate credentials before manually
removing `auth.json`.
