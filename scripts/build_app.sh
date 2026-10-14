#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "===> FlacToAlac macOS .app Derleme Aracı"

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ensure pyinstaller is installed
if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    echo "===> PyInstaller kuruluyor..."
    pip install pyinstaller
fi

# Ensure icon exists
if [ ! -f "assets/icon.icns" ]; then
    echo "===> Uygulama ikonu oluşturuluyor..."
    python3 scripts/generate_icon.py
fi

echo "===> PyInstaller ile macOS .app paketi oluşturuluyor..."
pyinstaller \
    --name "FlacToAlac" \
    --windowed \
    --noconfirm \
    --clean \
    --icon "assets/icon.icns" \
    --add-data "assets:assets" \
    main.py

echo "===> Derleme Başarılı!"
echo "Uygulama şurada hazır: $(pwd)/dist/FlacToAlac.app"
