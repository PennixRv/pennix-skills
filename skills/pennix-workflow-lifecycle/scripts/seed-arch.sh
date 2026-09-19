#!/usr/bin/env bash
set -euo pipefail

readonly CODEX_PACKAGE="openai-codex"
readonly CONFLICTING_CODEX_PACKAGE="openai-codex-bin"
readonly PROVIDER_ID="OpenAI"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly TEMPLATE_DIR="$SCRIPT_DIR/../templates"
readonly CONFIG_TEMPLATE="$TEMPLATE_DIR/config.toml.seed"
readonly AUTH_TEMPLATE="$TEMPLATE_DIR/auth.json.seed"
readonly CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
readonly CONFIG_FILE="$CODEX_HOME_DIR/config.toml"
readonly AUTH_FILE="$CODEX_HOME_DIR/auth.json"
CONFIG_CREATED=0
AUTH_CREATED=0

cleanup() {
  local status=$?
  if (( status != 0 )); then
    (( CONFIG_CREATED )) && rm -f "$CONFIG_FILE"
    (( AUTH_CREATED )) && rm -f "$AUTH_FILE"
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

require_template() {
  [[ -r "$1" && ! -L "$1" ]] || fail "required Codex template is missing or unsafe: $1"
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
  candidate="$(pacman -Si "$CODEX_PACKAGE" 2>/dev/null | awk '$1 == "Version" { print $3; exit }')"
  [[ -n "$candidate" ]] || fail "Arch official package is unavailable: $CODEX_PACKAGE"
  printf 'Arch official Codex candidate: %s\n' "$candidate"
  if (( EUID == 0 )); then
    pacman -Syu --needed "$CODEX_PACKAGE"
  else
    require_command sudo
    sudo pacman -Syu --needed "$CODEX_PACKAGE"
  fi
  require_command codex
}

require_fresh_codex_config() {
  [[ ! -e "$CONFIG_FILE" ]] || fail "existing Codex config found; Stage 0 refuses to overwrite: $CONFIG_FILE"
}

require_fresh_codex_auth() {
  [[ ! -e "$AUTH_FILE" ]] || fail "existing Codex auth cache found; Stage 0 refuses to overwrite: $AUTH_FILE"
}

require_fresh_codex_package() {
  if pacman -Qq "$CONFLICTING_CODEX_PACKAGE" >/dev/null 2>&1; then
    fail "conflicting Codex package is already installed; Stage 0 refuses package-owner migration: $CONFLICTING_CODEX_PACKAGE"
  fi
}

configure_provider() {
  require_fresh_codex_config
  require_fresh_codex_auth
  require_template "$CONFIG_TEMPLATE"
  require_template "$AUTH_TEMPLATE"
  if [[ ! -d "$CODEX_HOME_DIR" ]]; then
    mkdir -p "$CODEX_HOME_DIR"
    chmod 700 "$CODEX_HOME_DIR"
  fi

  local base_url api_key
  read -r -p "OpenAI-compatible base URL: " base_url
  [[ "$base_url" =~ ^https?://[^[:space:]]+$ ]] || fail "base URL must be an absolute HTTP(S) URL"
  read -r -s -p "API key (hidden): " api_key
  printf '\n'
  [[ -n "$api_key" ]] || fail "API key cannot be empty"

  [[ "$base_url" != *$'\n'* && "$base_url" != *$'\r'* && "$base_url" != *'"'* && "$base_url" != *\\* ]] || fail "base URL contains unsupported TOML characters"
  local escaped_key
  escaped_key="$(json_string "$api_key")"
  write_file_atomic "$CONFIG_FILE" < <(render_seed_template "$CONFIG_TEMPLATE" "$base_url" "")
  CONFIG_CREATED=1
  write_file_atomic "$AUTH_FILE" < <(render_seed_template "$AUTH_TEMPLATE" "" "$escaped_key")
  AUTH_CREATED=1
  unset api_key
}

print_next_step() {
  cat <<EOF

Pennix workflow seed complete. Start a new Codex session, then paste:

请先安装 Pennix Skills，然后使用 `pennix-workflow-lifecycle` 开始部署 Pennix 工作流。
先执行只读 `discover`，核对宿主、组件 owner 和版本 catalog；
再明确选择一个组件执行 install、upgrade 或 uninstall。
EOF
}

main() {
  umask 077
  require_arch_wsl2_or_native
  require_safe_codex_home
  require_fresh_codex_config
  require_fresh_codex_auth
  require_command pacman
  require_fresh_codex_package
  install_codex
  configure_provider
  print_next_step
}

main "$@"
