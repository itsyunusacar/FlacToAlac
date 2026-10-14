#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "===> FlacToAlac macOS .app Builder"

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ensure pyinstaller is installed
if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    echo "===> Installing PyInstaller..."
    pip install pyinstaller
fi

# Ensure icon exists
if [ ! -f "assets/icon.icns" ]; then
    echo "===> Generating application icon..."
    python3 scripts/generate_icon.py
fi

echo "===> Bundling macOS .app package via PyInstaller..."
pyinstaller \
    --name "FlacToAlac" \
    --windowed \
    --noconfirm \
    --clean \
    --icon "assets/icon.icns" \
    --add-data "assets:assets" \
    main.py

echo "===> Build Succeeded!"
echo "App is available at: $(pwd)/dist/FlacToAlac.app"
