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
"$SCRIPT_DIR/scripts/kali-mcp-manager.sh" start

# Default NVIDIA NIM settings (API keys should live in .env or shell environment)
export NVIDIA_BASE_URL="${NVIDIA_BASE_URL:-https://integrate.api.nvidia.com/v1}"
export NVIDIA_MODEL="${NVIDIA_MODEL:-nvidia/nemotron-3-nano-omni-30b-a3b-reasoning}"

# Proxy bypass for localhost
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="localhost,127.0.0.1"

# Resolve a Python 3 interpreter that has PySide6 (QtCore/QtGui/QtWidgets) + core deps
resolve_python() {
    local candidates=()
    [ -x "$SCRIPT_DIR/.venv/bin/python3" ] && candidates+=("$SCRIPT_DIR/.venv/bin/python3")
    if command -v python3 >/dev/null 2>&1; then
        candidates+=("$(command -v python3)")
    fi
    [ -x "/usr/bin/python3" ] && candidates+=("/usr/bin/python3")
    [ -x "/usr/bin/python3.14" ] && candidates+=("/usr/bin/python3.14")

    local py
    for py in "${candidates[@]}"; do
        if "$py" -c "import PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, openai, requests" >/dev/null 2>&1; then
            echo "$py"
            return 0
        fi
    done
    return 1
}

if ! PYTHON_BIN="$(resolve_python)"; then
    echo "ERROR: No Python 3 interpreter found with PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, openai, and requests." >&2
    echo "Fix on Kali/Debian:" >&2
    echo "  sudo apt install -y python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets" >&2
    echo "Or install into user site-packages:" >&2
    echo "  /usr/bin/python3 -m pip install --user --break-system-packages PySide6-Essentials openai requests rich" >&2
    exit 1
fi

# Launch the Desktop GUI
exec "$PYTHON_BIN" "$SCRIPT_DIR/app/kali-gui.py" "$@"
