#!/usr/bin/env bash
# install.sh — Configure the Freshservice MCP server for Claude Desktop on macOS

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${BOLD}$*${RESET}"; }
success() { echo -e "${GREEN}✓ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
error()   { echo -e "${RED}✗ $*${RESET}" >&2; }

# ── macOS check ───────────────────────────────────────────────────────────────
if [[ "$(uname)" != "Darwin" ]]; then
  error "This script is for macOS only."
  exit 1
fi

echo ""
echo -e "${BOLD}Freshservice MCP — Claude Desktop Setup${RESET}"
echo "──────────────────────────────────────────"
echo ""

# ── Prompt for repo directory ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while true; do
  read -rp "$(echo -e "${BOLD}Path to freshservice-mcp folder${RESET} [${SCRIPT_DIR}]: ")" REPO_DIR

  # Default to the script's own directory if user presses Enter
  REPO_DIR="${REPO_DIR:-$SCRIPT_DIR}"

  # Expand ~ if present
  REPO_DIR="${REPO_DIR/#\~/$HOME}"

  # Strip trailing slash
  REPO_DIR="${REPO_DIR%/}"

  if [[ ! -d "$REPO_DIR" ]]; then
    warn "Directory not found: $REPO_DIR — please try again."
    continue
  fi

  if [[ ! -f "$REPO_DIR/pyproject.toml" ]]; then
    warn "$REPO_DIR doesn't look like the freshservice-mcp repo (pyproject.toml not found)."
    read -rp "Continue anyway? [y/N]: " CONFIRM
    [[ "$CONFIRM" =~ ^[Yy]$ ]] && break || continue
  fi

  break
done

success "Repo path: $REPO_DIR"
echo ""

# ── Check uv is installed ─────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  error "uv is not installed. Install it first:"
  echo "  brew install uv"
  echo "  or: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi
success "uv found at $(command -v uv)"
echo ""

# ── Prompt for Freshservice domain ────────────────────────────────────────────
while true; do
  read -rp "$(echo -e "${BOLD}Freshservice domain${RESET} (e.g. yourcompany.freshservice.com): ")" FS_DOMAIN

  # Strip protocol and trailing slash if user included them
  FS_DOMAIN="${FS_DOMAIN#https://}"
  FS_DOMAIN="${FS_DOMAIN#http://}"
  FS_DOMAIN="${FS_DOMAIN%/}"
  FS_DOMAIN="$(echo "$FS_DOMAIN" | xargs)"  # trim whitespace

  if [[ -z "$FS_DOMAIN" ]]; then
    warn "Domain cannot be empty. Please try again."
    continue
  fi

  if [[ "$FS_DOMAIN" != *.freshservice.com ]]; then
    warn "That domain doesn't look like a Freshservice domain (expected *.freshservice.com)."
    read -rp "Continue anyway? [y/N]: " CONFIRM
    [[ "$CONFIRM" =~ ^[Yy]$ ]] && break || continue
  fi

  break
done

# ── Prompt for API key (hidden input) ─────────────────────────────────────────
echo ""
while true; do
  read -rsp "$(echo -e "${BOLD}Freshservice API key${RESET} (input hidden): ")" FS_APIKEY
  echo ""

  if [[ -z "$FS_APIKEY" ]]; then
    warn "API key cannot be empty. Please try again."
    continue
  fi

  if [[ "${#FS_APIKEY}" -lt 10 ]]; then
    warn "That API key looks too short. Freshservice API keys are usually 20+ characters."
    read -rp "Continue anyway? [y/N]: " CONFIRM
    [[ "$CONFIRM" =~ ^[Yy]$ ]] && break || continue
  fi

  break
done

echo ""

# ── Claude Desktop config file ────────────────────────────────────────────────
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

mkdir -p "$CONFIG_DIR"

# Create the file with an empty object if it doesn't exist
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo '{}' > "$CONFIG_FILE"
  success "Created $CONFIG_FILE"
else
  # Backup existing config
  BACKUP="${CONFIG_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
  cp "$CONFIG_FILE" "$BACKUP"
  success "Backed up existing config to $(basename "$BACKUP")"
fi

# ── Merge config using Python (always available on macOS) ─────────────────────
python3 - "$CONFIG_FILE" "$REPO_DIR" "$FS_APIKEY" "$FS_DOMAIN" <<'PYEOF'
import json
import sys

config_path, repo_dir, api_key, domain = sys.argv[1:]

with open(config_path, "r") as f:
    content = f.read().strip()

try:
    config = json.loads(content) if content else {}
except json.JSONDecodeError:
    print("ERROR: Existing config file contains invalid JSON. Please fix it manually.", file=sys.stderr)
    sys.exit(1)

if not isinstance(config, dict):
    config = {}

config.setdefault("mcpServers", {})

config["mcpServers"]["freshservice"] = {
    "command": "uv",
    "args": [
        "run",
        "--directory",
        repo_dir,
        "freshservice-mcp"
    ],
    "env": {
        "FRESHSERVICE_APIKEY": api_key,
        "FRESHSERVICE_DOMAIN": domain
    }
}

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")

print("ok")
PYEOF

if [[ $? -ne 0 ]]; then
  error "Failed to update config. Your original config is unchanged."
  exit 1
fi

success "Config written to $CONFIG_FILE"

# ── Quick connectivity test ───────────────────────────────────────────────────
echo ""
info "Testing API connectivity..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${FS_APIKEY}:X" \
  "https://${FS_DOMAIN}/api/v2/tickets?per_page=1" \
  --max-time 10 2>/dev/null || echo "000")

case "$HTTP_STATUS" in
  200) success "API connection successful (HTTP 200)" ;;
  401) warn "HTTP 401 — API key looks incorrect. Check it in Freshservice → Profile Settings." ;;
  403) warn "HTTP 403 — Access denied. Verify your domain and API key are correct." ;;
  404) warn "HTTP 404 — Domain not found. Double-check: $FS_DOMAIN" ;;
  000) warn "Could not reach $FS_DOMAIN — check your network connection." ;;
  *)   warn "Unexpected HTTP $HTTP_STATUS from Freshservice API." ;;
esac

# ── Offer to restart Claude Desktop ──────────────────────────────────────────
echo ""
if pgrep -x "Claude" &>/dev/null; then
  read -rp "$(echo -e "${BOLD}Restart Claude Desktop now?${RESET} [Y/n]: ")" RESTART
  if [[ ! "$RESTART" =~ ^[Nn]$ ]]; then
    osascript -e 'quit app "Claude"' 2>/dev/null || true
    sleep 2
    open -a "Claude"
    success "Claude Desktop restarted"
  else
    warn "Remember to restart Claude Desktop manually for the changes to take effect."
  fi
else
  info "Claude Desktop is not running. Open it when you're ready."
fi

echo ""
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo "You can now ask Claude about your Freshservice tickets, changes, assets, and more."
echo ""
