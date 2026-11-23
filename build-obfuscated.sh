#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src_private"

if ! command -v pyarmor >/dev/null 2>&1; then
    echo "ERROR: pyarmor is not installed or not in PATH." >&2
    exit 1
fi

if [ ! -d "$SRC_DIR" ]; then
    echo "ERROR: Source directory not found: $SRC_DIR" >&2
    echo "Place editable .py source files in src_private/ before building." >&2
    exit 1
fi

shopt -s nullglob
SRC_FILES=("$SRC_DIR"/*.py)
shopt -u nullglob

if [ "${#SRC_FILES[@]}" -eq 0 ]; then
    echo "ERROR: No .py source files found in $SRC_DIR" >&2
    exit 1
fi

# Use user-specified PYARMOR_HOME, or $HOME/.pyarmor if writable, else /tmp/pyarmor_home
if [ -z "${PYARMOR_HOME:-}" ]; then
    if [ -n "${HOME:-}" ] \
        && mkdir -p "$HOME/.pyarmor" 2>/dev/null \
        && touch "$HOME/.pyarmor/.write_test" 2>/dev/null; then
        rm -f "$HOME/.pyarmor/.write_test"
        PYARMOR_HOME="$HOME/.pyarmor"
    else
        PYARMOR_HOME="/tmp/pyarmor_home"
    fi
fi
mkdir -p "$PYARMOR_HOME"
export PYARMOR_HOME

echo "[1/4] Cleaning previous pyarmor_runtime_* directories..."
rm -rf "$SCRIPT_DIR"/pyarmor_runtime_*

echo "[2/4] Obfuscating ${#SRC_FILES[@]} Python module(s) from src_private/ -> repo root..."
pyarmor gen -O "$SCRIPT_DIR" "${SRC_FILES[@]}"

echo "[3/4] Restoring executable permissions on CLI/GUI entrypoints..."
for entry in "$SCRIPT_DIR/kali-gui.py" "$SCRIPT_DIR/kali-agent.py"; do
    if [ -f "$entry" ]; then
        chmod +x "$entry"
    fi
done

echo "[4/4] Running built-in obfuscation leak checks..."
shopt -s nullglob
RUNTIME_LIBS=("$SCRIPT_DIR"/pyarmor_runtime_*/pyarmor_runtime.so)
ROOT_PY_FILES=("$SCRIPT_DIR"/*.py)
shopt -u nullglob

if [ "${#RUNTIME_LIBS[@]}" -eq 0 ]; then
    echo "ERROR: pyarmor_runtime.so was not generated in $SCRIPT_DIR" >&2
    exit 1
fi

if [ "${#ROOT_PY_FILES[@]}" -eq 0 ]; then
    echo "ERROR: No obfuscated .py files found in $SCRIPT_DIR" >&2
    exit 1
fi

LEAK_PATTERNS=(
    "def run_chat_turn"
    "class KaliGuiWindow"
    "PROVIDER_REGISTRY"
    "DARK_STYLESHEET"
    "SYSTEM_PROMPT"
)

FAIL=0
for pyf in "${ROOT_PY_FILES[@]}"; do
    base="$(basename "$pyf")"
    header="$(head -n 3 "$pyf")"
    if [[ "$header" != *"# Pyarmor "* ]]; then
        echo "FAIL: $base missing PyArmor header" >&2
        FAIL=1
    fi
    if ! grep -q "__pyarmor__" "$pyf"; then
        echo "FAIL: $base missing __pyarmor__ bootstrap" >&2
        FAIL=1
    fi
    for pat in "${LEAK_PATTERNS[@]}"; do
        if grep -Fq "$pat" "$pyf"; then
            echo "FAIL: $base leaked plaintext string: $pat" >&2
            FAIL=1
        fi
    done
done

if [ "$FAIL" -ne 0 ]; then
    echo "ERROR: Obfuscation verification failed!" >&2
    exit 1
fi

echo "OK: Obfuscated ${#ROOT_PY_FILES[@]} root .py files cleanly with PyArmor (PYARMOR_HOME=$PYARMOR_HOME)."
