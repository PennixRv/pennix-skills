#!/usr/bin/env bash
set -euo pipefail

readonly CODEX_PACKAGE="openai-codex-bin"
readonly CODEX_REPLACEMENT_PACKAGE="openai-codex"
readonly PROVIDER_ID="OpenAI"
readonly REMOTE_TEMPLATE_BASE_URL="https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/templates"
SCRIPT_SOURCE="${BASH_SOURCE[0]-}"
SCRIPT_DIR=""
if [[ -n "$SCRIPT_SOURCE" && -f "$SCRIPT_SOURCE" ]]; then
  SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_SOURCE")" && pwd)"
fi
readonly SCRIPT_DIR
readonly TEMPLATE_DIR="${SCRIPT_DIR:+$SCRIPT_DIR/../templates}"
readonly CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
readonly CONFIG_FILE="$CODEX_HOME_DIR/config.toml"
readonly AUTH_FILE="$CODEX_HOME_DIR/auth.json"
CONFIG_TEMPLATE="${TEMPLATE_DIR:+$TEMPLATE_DIR/config.toml.seed}"
AUTH_TEMPLATE="${TEMPLATE_DIR:+$TEMPLATE_DIR/auth.json.seed}"
REMOTE_TEMPLATE_DIR=""
AUR_BOOTSTRAP_DIR=""
AUR_HELPER=""
PROMPT_FD=0
REMOTE_MODE=0
CONFIG_CREATED=0
AUTH_CREATED=0
CODEX_REPLACEMENT_PRESENT=0

cleanup() {
  local status=$?
  if (( status != 0 )); then
    (( CONFIG_CREATED )) && rm -f "$CONFIG_FILE"
    (( AUTH_CREATED )) && rm -f "$AUTH_FILE"
  fi
  if [[ -n "$REMOTE_TEMPLATE_DIR" ]]; then
    rm -f "$REMOTE_TEMPLATE_DIR/config.toml.seed" "$REMOTE_TEMPLATE_DIR/auth.json.seed"
    rmdir "$REMOTE_TEMPLATE_DIR" 2>/dev/null || true
  fi
  if [[ -n "$AUR_BOOTSTRAP_DIR" ]]; then
    rm -rf -- "$AUR_BOOTSTRAP_DIR"
  fi
  exit "$status"
}
trap cleanup EXIT

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 2
}

require_arch_wsl2_or_native() {
  [[ -r /etc/os-release ]] || fail "cannot read /etc/os-release"
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "arch" ]] || fail "Stage 0 supports Arch Linux only"

  local markers=""
  [[ -r /proc/sys/kernel/osrelease ]] && markers+="$(< /proc/sys/kernel/osrelease)\n"
  [[ -r /proc/version ]] && markers+="$(< /proc/version)\n"
  if grep -Eqi 'microsoft|wsl' <<<"$markers"; then
    grep -Eqi 'wsl2|microsoft-standard-wsl2' <<<"$markers" || fail "Arch Linux on WSL requires WSL2"
  fi
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command is missing: $1"
}

run_pacman() {
  if (( EUID == 0 )); then
    pacman "$@"
    return
  fi
  require_command sudo
  sudo pacman "$@"
}

require_template() {
  [[ -f "$1" && -r "$1" && ! -L "$1" ]] || fail "required Codex template is missing or unsafe: $1"
}

validate_template_contract() {
  local config_content auth_content
  config_content="$(<"$CONFIG_TEMPLATE")"
  auth_content="$(<"$AUTH_TEMPLATE")"
  [[ "$config_content" == *'{{PENNIX_BASE_URL}}'* ]] || fail "Codex config template is missing the base URL placeholder"
  [[ "$auth_content" == *'{{PENNIX_API_KEY}}'* ]] || fail "Codex auth template is missing the API key placeholder"
}

resolve_templates() {
  if [[ -f "$CONFIG_TEMPLATE" && -f "$AUTH_TEMPLATE" && ! -L "$CONFIG_TEMPLATE" && ! -L "$AUTH_TEMPLATE" ]]; then
    validate_template_contract
    return
  fi

  REMOTE_MODE=1
  require_command curl
  REMOTE_TEMPLATE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pennix-seed.XXXXXX")" || fail "cannot create a temporary template directory"
  local base_url="$REMOTE_TEMPLATE_BASE_URL"
  [[ "$base_url" =~ ^https://[^[:space:]]+$ ]] || fail "seed template base URL must use HTTPS"
  local template_name
  for template_name in config.toml.seed auth.json.seed; do
    curl -fsSL --proto '=https' --tlsv1.2 --max-time 30 \
      "$base_url/$template_name" -o "$REMOTE_TEMPLATE_DIR/$template_name" \
      || fail "cannot download the remote Codex template: $template_name"
    require_template "$REMOTE_TEMPLATE_DIR/$template_name"
  done
  CONFIG_TEMPLATE="$REMOTE_TEMPLATE_DIR/config.toml.seed"
  AUTH_TEMPLATE="$REMOTE_TEMPLATE_DIR/auth.json.seed"
  validate_template_contract
}

open_prompt_fd() {
  if (( ! REMOTE_MODE )); then
    PROMPT_FD=0
    return
  fi
  [[ -r /dev/tty && -w /dev/tty ]] || fail "remote seed requires an interactive control terminal (/dev/tty)"
  exec {PROMPT_FD}</dev/tty || fail "cannot open the interactive control terminal (/dev/tty)"
}

prompt_read() {
  local prompt="$1"
  local variable="$2"
  if (( PROMPT_FD == 0 )); then
    IFS= read -r -p "$prompt" "$variable" || fail "interactive input ended before seed configuration completed"
  else
    IFS= read -r -u "$PROMPT_FD" -p "$prompt" "$variable" || fail "interactive input ended before seed configuration completed"
  fi
}

prompt_read_secret() {
  local prompt="$1"
  local variable="$2"
  if (( PROMPT_FD == 0 )); then
    IFS= read -r -s -p "$prompt" "$variable" || fail "interactive input ended before seed configuration completed"
  else
    IFS= read -r -s -u "$PROMPT_FD" -p "$prompt" "$variable" || fail "interactive input ended before seed configuration completed"
  fi
}

require_safe_codex_home() {
  [[ "$CODEX_HOME_DIR" == /* ]] || fail "CODEX_HOME must be an absolute path"
  local current="$CODEX_HOME_DIR"
  while :; do
    [[ ! -L "$current" ]] || fail "CODEX_HOME must not traverse a symbolic link: $current"
    [[ "$current" == / ]] && break
    current="${current%/*}"
    [[ -n "$current" ]] || current="/"
  done
  [[ ! -e "$CODEX_HOME_DIR" || -d "$CODEX_HOME_DIR" ]] || fail "CODEX_HOME is not a directory: $CODEX_HOME_DIR"
}

json_string() {
  local value="$1"
  [[ "$value" != *[[:cntrl:]]* ]] || fail "API key contains an unsupported control character"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "$value"
}

render_seed_template() {
  local template="$1"
  local base_url="$2"
  local api_key="$3"
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line//\{\{PENNIX_BASE_URL\}\}/$base_url}"
    line="${line//\{\{PENNIX_API_KEY\}\}/$api_key}"
    printf '%s\n' "$line"
  done <"$template"
}

write_file_atomic() {
  local destination="$1"
  local temporary
  temporary="$(mktemp "${destination}.tmp.XXXXXX")"
  trap 'rm -f "$temporary"' RETURN
  cat >"$temporary"
  chmod 600 "$temporary"
  mv -f "$temporary" "$destination"
  trap - RETURN
}

install_codex() {
  local candidate
  run_pacman -S --needed --noconfirm npm
  select_aur_helper
  if (( CODEX_REPLACEMENT_PRESENT )); then
    printf 'Migrating Codex package owner: %s -> %s\n' "$CODEX_REPLACEMENT_PACKAGE" "$CODEX_PACKAGE"
    "$AUR_HELPER" -R --noconfirm "$CODEX_REPLACEMENT_PACKAGE" \
      || fail "Codex package-owner migration failed: $CODEX_REPLACEMENT_PACKAGE"
  fi
  candidate="$("$AUR_HELPER" -Si "$CODEX_PACKAGE" 2>/dev/null | awk '$1 == "Version" { version=$3 } END { if (version) print version }')"
  [[ -n "$candidate" ]] || fail "AUR Codex package is unavailable: $CODEX_PACKAGE"
  printf 'AUR Codex candidate: %s\n' "$candidate"
  "$AUR_HELPER" -Syu --needed --noconfirm "$CODEX_PACKAGE"
  require_command codex
}

bootstrap_yay() {
  (( EUID != 0 )) || fail "Stage 0 cannot bootstrap an AUR helper as root"
  run_pacman -S --needed --noconfirm base-devel git
  require_command git
  require_command makepkg
  AUR_BOOTSTRAP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pennix-yay.XXXXXX")" || fail "cannot create an AUR helper build directory"
  git clone --depth 1 https://aur.archlinux.org/yay.git "$AUR_BOOTSTRAP_DIR/yay" \
    || fail "cannot clone the yay AUR package"
  (cd "$AUR_BOOTSTRAP_DIR/yay" && makepkg -si --needed --noconfirm) \
    || fail "cannot build the yay AUR helper"
  require_command yay
  AUR_HELPER="yay"
}

select_aur_helper() {
  if command -v yay >/dev/null 2>&1; then
    AUR_HELPER="yay"
    return
  fi
  if command -v paru >/dev/null 2>&1; then
    AUR_HELPER="paru"
    return
  fi
  bootstrap_yay
}

detect_codex_replacement() {
  if pacman -Qq | awk -v package="$CODEX_REPLACEMENT_PACKAGE" \
    '$0 == package { found=1 } END { exit !found }'; then
    CODEX_REPLACEMENT_PRESENT=1
  fi
}

configure_provider() {
  local needs_config=0 needs_auth=0
  [[ -e "$CONFIG_FILE" ]] || needs_config=1
  [[ -e "$AUTH_FILE" ]] || needs_auth=1
  if (( ! needs_config && ! needs_auth )); then
    return 0
  fi

  require_template "$CONFIG_TEMPLATE"
  require_template "$AUTH_TEMPLATE"
  if [[ ! -d "$CODEX_HOME_DIR" ]]; then
    mkdir -p "$CODEX_HOME_DIR"
    chmod 700 "$CODEX_HOME_DIR"
  fi

  local base_url api_key escaped_key
  if (( needs_config )); then
    prompt_read "OpenAI-compatible base URL: " base_url
    [[ "$base_url" =~ ^https?://[^[:space:]]+$ ]] || fail "base URL must be an absolute HTTP(S) URL"
    [[ "$base_url" != *$'\n'* && "$base_url" != *$'\r'* && "$base_url" != *'"'* && "$base_url" != *\\* ]] || fail "base URL contains unsupported TOML characters"
    write_file_atomic "$CONFIG_FILE" < <(render_seed_template "$CONFIG_TEMPLATE" "$base_url" "")
    CONFIG_CREATED=1
  fi

  if (( needs_auth )); then
    prompt_read_secret "API key (hidden): " api_key
    printf '\n'
    [[ -n "$api_key" ]] || fail "API key cannot be empty"
    escaped_key="$(json_string "$api_key")"
    write_file_atomic "$AUTH_FILE" < <(render_seed_template "$AUTH_TEMPLATE" "" "$escaped_key")
    AUTH_CREATED=1
    unset api_key
  fi
}

print_next_step() {
  cat <<'EOF'

Pennix workflow seed complete.

Start one new Codex session. In its first turn, paste exactly:

请使用系统内置 `$skill-installer`，从 `PennixRv/pennix-skills` 的 `main` 将 `skills/pennix-workflow-lifecycle` 安装到 `$CODEX_HOME/skills/pennix-skills`（传为 `--dest`）。这是 Pennix 的 bootstrap Skill；不要安装其他 Pennix Skills，也不要假定它会在本轮对话可用。

After `$skill-installer` confirms success, stay in that same Codex session. In its next turn, paste exactly:

使用 `$pennix-workflow-lifecycle` 完整部署 Pennix 工作流。先执行只读 `discover`；若 collection 处于 bootstrap 状态，按该 Skill 的 catalog 合同通过系统 `$skill-installer` 补齐 collection，然后继续部署。
EOF
}

main() {
  (( $# == 0 )) || fail "seed only supports initial installation; use pennix-workflow-lifecycle for component uninstall"
  umask 077
  require_arch_wsl2_or_native
  require_safe_codex_home
  require_command pacman
  detect_codex_replacement
  if [[ ! -e "$CONFIG_FILE" || ! -e "$AUTH_FILE" ]]; then
    resolve_templates
    open_prompt_fd
  fi
  install_codex
  configure_provider
  print_next_step
}

main "$@"
