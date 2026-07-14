#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uv tool install --upgrade khmerthings
printf '%s\n' "Installed khmerthings. Run: khmerthings --help"
