#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
MAN_DIR="$PREFIX/share/man/man1"

mkdir -p "$BIN_DIR" "$MAN_DIR"

install -m 0755 "$SCRIPT_DIR/adb_auto.py" "$BIN_DIR/adb-auto"
if [ -f "$SCRIPT_DIR/man/adb-auto.1" ]; then
    gzip -c "$SCRIPT_DIR/man/adb-auto.1" > "$MAN_DIR/adb-auto.1.gz"
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    if [ -f "$HOME/.bashrc" ] && ! grep -q "$BIN_DIR" "$HOME/.bashrc"; then
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
        echo "[✓] Added $BIN_DIR to PATH in ~/.bashrc"
    fi
fi

echo "[✓] Installed adb-auto to $BIN_DIR/adb-auto"
echo "[✓] Installed man page to $MAN_DIR/adb-auto.1.gz"
echo "Run 'adb-auto --help' or 'man adb-auto' to get started."
