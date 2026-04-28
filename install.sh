#!/bin/bash
# Simple wrapper script to run Firefox installer with proper privileges

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/install_firefox.py"

if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required but not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

if [ ! -f "$INSTALLER" ]; then
    echo "Error: install_firefox.py not found in $SCRIPT_DIR"
    exit 1
fi

if [[ "${1:-}" == "--version" ]]; then
    python3 "$INSTALLER" --version
    exit 0
fi

if [[ "${1:-}" == "check" ]]; then
    python3 "$INSTALLER" check
    exit $?
fi

if [[ "${1:-}" == "detect" ]]; then
    python3 "$INSTALLER" detect
    exit $?
fi

if [[ "${1:-}" == "uninstall" ]]; then
    if [ "$EUID" -eq 0 ]; then
        python3 "$INSTALLER" uninstall
    else
        echo "This command requires root privileges. Running with sudo..."
        sudo python3 "$INSTALLER" uninstall
    fi
    exit $?
fi

INSTALL_ARGS=("$@")
if [[ "${1:-}" == "install" ]]; then
    INSTALL_ARGS=("${@:2}")
fi

# Run with sudo if not already root
if [ "$EUID" -eq 0 ]; then
    python3 "$INSTALLER" install "${INSTALL_ARGS[@]}"
else
    echo "This script requires root privileges. Running with sudo..."
    sudo python3 "$INSTALLER" install "${INSTALL_ARGS[@]}"
fi
