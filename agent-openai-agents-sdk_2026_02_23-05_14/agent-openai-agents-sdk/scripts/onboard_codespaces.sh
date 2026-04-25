#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "[onboard] $1"; }
log_ok() { echo -e "${GREEN}[onboard] ✓ $1${NC}"; }
log_warn() { echo -e "${YELLOW}[onboard] ⚠ $1${NC}"; }
log_err() { echo -e "${RED}[onboard] ✗ $1${NC}"; }

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    log_ok "uv is installed ($(uv --version 2>/dev/null || echo unknown))"
    return
  fi

  log_info "uv not found; installing..."
  if curl -LsSf https://astral.sh/uv/install.sh | sh; then
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  fi

  if command -v uv >/dev/null 2>&1; then
    log_ok "uv installed ($(uv --version 2>/dev/null || echo unknown))"
  else
    log_err "Failed to install uv. Install manually: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
  fi
}

ensure_databricks_cli() {
  if command -v databricks >/dev/null 2>&1; then
    log_ok "Databricks CLI is installed"
    return
  fi

  log_info "Databricks CLI not found; installing..."
  if curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh; then
    if command -v databricks >/dev/null 2>&1; then
      log_ok "Databricks CLI installed"
      return
    fi
  fi

  log_warn "Databricks CLI install did not complete. You can install it later; local OpenAI mode can still run."
}

setup_env_file() {
  if [[ -f .env ]]; then
    log_ok ".env already exists"
    return
  fi

  if [[ -f .env.example ]]; then
    cp .env.example .env
    log_ok "Created .env from .env.example"
  else
    cat > .env <<'EOF'
AGENT_BACKEND=openai
AGENT_MODEL=gpt-4.1-mini
MLFLOW_TRACKING_URI="databricks"
MLFLOW_REGISTRY_URI="databricks-uc"
EOF
    log_warn "Created minimal .env because .env.example was not found"
  fi
}

set_env_value() {
  local key="$1"
  local value="$2"

  if grep -qE "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    printf "\n%s=%s\n" "$key" "$value" >> .env
  fi
}

configure_from_secrets() {
  local configured_any=false

  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    set_env_value "OPENAI_API_KEY" "$OPENAI_API_KEY"
    configured_any=true
    log_ok "Configured OPENAI_API_KEY from Codespaces environment"
  fi

  if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
    set_env_value "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY"
    configured_any=true
    log_ok "Configured OPENROUTER_API_KEY from Codespaces environment"
  fi

  if [[ "$configured_any" == true ]]; then
    set_env_value "AGENT_BACKEND" "openai"
    log_ok "Set AGENT_BACKEND=openai"
  else
    log_warn "No OPENAI_API_KEY/OPENROUTER_API_KEY found in environment; set one in .env before running the app"
  fi
}

configure_databricks_profile() {
  if ! command -v databricks >/dev/null 2>&1; then
    return
  fi

  if databricks auth profiles >/dev/null 2>&1; then
    set_env_value "DATABRICKS_CONFIG_PROFILE" "DEFAULT"
    log_ok "Databricks CLI profiles detected (DEFAULT profile set in .env)"
  else
    log_warn "No Databricks auth profiles found yet. Run 'databricks auth login' when you need Databricks mode."
  fi
}

install_dependencies() {
  log_info "Installing Python dependencies with uv sync..."
  uv sync
  log_ok "Dependencies installed"
}

print_next_steps() {
  echo
  echo "========================================"
  echo "Codespaces onboarding complete"
  echo "========================================"
  echo
  echo "Next commands:"
  echo "  uv run verify-setup"
  echo "  uv run start-app"
  echo
}

main() {
  log_info "Starting Codespaces onboarding in $ROOT_DIR"
  ensure_uv
  ensure_databricks_cli
  setup_env_file
  configure_from_secrets
  configure_databricks_profile
  install_dependencies
  print_next_steps
}

main "$@"
