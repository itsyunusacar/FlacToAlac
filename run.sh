#!/usr/bin/env bash
set -e

# Change directory to project root
cd "$(dirname "$0")"

# Find python3 in PATH or /usr/local/bin
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif [ -f "/usr/local/bin/python3" ]; then
    PY_BIN="/usr/local/bin/python3"
else
    echo "Hata: python3 bulunamadı!"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "İlk kurulum yapılıyor: Sanal ortam (.venv) oluşturuluyor..."
    $PY_BIN -m venv .venv
    chflags -R nohidden .venv 2>/dev/null || true
    source .venv/bin/activate
    pip install -r requirements.txt
else
    chflags -R nohidden .venv 2>/dev/null || true
    source .venv/bin/activate
fi

# Run application
python3 main.py
