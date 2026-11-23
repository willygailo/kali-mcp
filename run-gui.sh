#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load local .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Ensure kali-server-mcp is running
"$SCRIPT_DIR/kali-mcp-manager.sh" start

# Default NVIDIA NIM settings (API keys should live in .env or shell environment)
export NVIDIA_BASE_URL="${NVIDIA_BASE_URL:-https://integrate.api.nvidia.com/v1}"
export NVIDIA_MODEL="${NVIDIA_MODEL:-nvidia/nemotron-3-nano-omni-30b-a3b-reasoning}"

# Proxy bypass for localhost
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="localhost,127.0.0.1"

# Launch the Desktop GUI
python3 "$SCRIPT_DIR/kali-gui.py" "$@"
