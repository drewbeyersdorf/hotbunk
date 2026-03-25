#!/usr/bin/env bash
set -euo pipefail

HOTBUNK_DIR="$HOME/.hotbunk"
VENV_DIR="$HOTBUNK_DIR/.venv"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "hotbunk installer"
echo "================="
echo ""

# Check Python version
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.12+ first."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]; }; then
    echo "Error: Python 3.12+ required, found $PY_VERSION"
    exit 1
fi

echo "Python $PY_VERSION -- OK"

# Create hotbunk directory
mkdir -p "$HOTBUNK_DIR"

# Check for pipx first, fall back to venv
if command -v pipx &>/dev/null; then
    echo "Installing with pipx..."
    pipx install "$REPO_DIR"
    echo ""
    echo "Installed via pipx. The 'hotbunk' command should already be on your PATH."
else
    echo "Creating venv at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"

    echo "Installing hotbunk..."
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet "$REPO_DIR"

    echo ""
    echo "Installed to $VENV_DIR"

    # Check if the bin dir is already on PATH
    if [[ ":$PATH:" != *":$VENV_DIR/bin:"* ]]; then
        echo ""
        echo "Add hotbunk to your PATH by adding this to your shell config:"
        echo ""
        echo "  export PATH=\"$VENV_DIR/bin:\$PATH\""
        echo ""
    fi
fi

echo ""
echo "Next steps"
echo "----------"
echo "1. Log in to your Claude account:"
echo "   claude auth login --email you@example.com"
echo ""
echo "2. Register it with hotbunk:"
echo "   hotbunk register my-account --email you@example.com"
echo ""
echo "3. Check status:"
echo "   hotbunk status"
