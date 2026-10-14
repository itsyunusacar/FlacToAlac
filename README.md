# 🎵 FlacToAlac

> **Modern, Bit-Perfect Lossless FLAC to ALAC (Apple Lossless M4A) Audio Converter with Drag & Drop.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Platform: macOS | Windows | Linux](https://img.shields.io/badge/Platform-macOS%20|%20Windows%20|%20Linux-lightgrey.svg)]()
[![Code: Lossless](https://img.shields.io/badge/Audio-100%25%20Bit--Perfect%20Lossless-orange.svg)]()
[![Build & Test](https://github.com/itsyunusacar/FlacToAlac/actions/workflows/tests.yml/badge.svg)](https://github.com/itsyunusacar/FlacToAlac/actions/workflows/tests.yml)

<p align="center">
  <img src="assets/icon.png" width="140" alt="FlacToAlac Logo" />
</p>

---

## 📖 Overview

**FlacToAlac** is a lightweight, modern desktop application designed to batch convert your FLAC music archive into **ALAC (Apple Lossless Audio Codec in `.m4a` container)** format. Converted tracks seamlessly sync across Apple devices (Apple Music, macOS, iOS, iPadOS, iPod) while maintaining **100% bit-perfect audio quality**.

---

## ✨ Features

- **Window-Wide Drag & Drop:** Drop audio files or nested folders anywhere on the application window to automatically queue FLAC files.
- **100% Lossless Bit-Perfect Conversion:** Direct transcode from FLAC to ALAC using native FFmpeg audio frames without resampling or acoustic loss.
- **Full Metadata & Tag Preservation:** Automatically transfers Title, Artist, Album, Year, Track/Disc numbers, Genre, and embedded tags.
- **Custom Album Artwork Selection:** Easily choose or drag & drop custom cover art (`.jpg`, `.png`, `.webp`) to embed across your files.
- **macOS Apple Music Integration:** Optionally imports converted `.m4a` files directly into your Apple Music library upon completion.
- **Multi-threaded Performance:** Configurable CPU worker threads with real-time conversion speed (`files/sec`) and Remaining Time (ETA) calculation.
- **Smart Skip Existing:** Detects already-converted `.m4a` files in destination directories to prevent redundant processing.
- **Queue Control & Error Log Viewer:** Select and remove tracks (`Delete`/`Backspace`), right-click context menu, and double-click to view complete FFmpeg diagnostic logs.
- **Safe Source Deletion:** Optional toggle to delete source `.flac` files only after successful conversion and integrity verification.
- **Zero Configuration:** Automatically locates system FFmpeg or falls back to bundled `imageio-ffmpeg` without manual setup.

---

## 🚀 Quick Start (macOS)

Clone the repository and launch the application:

```bash
git clone https://github.com/itsyunusacar/FlacToAlac.git
cd FlacToAlac
chmod +x run.sh
./run.sh
```

*(The `run.sh` script automatically sets up the Python virtual environment, installs dependencies, and launches the app.)*

### Manual Installation (macOS / Linux / Windows)

```bash
# 1. Clone repository
git clone https://github.com/itsyunusacar/FlacToAlac.git
cd FlacToAlac

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch application
python3 main.py
```

---

## 📦 Standalone macOS `.app` Bundle

You can package the application into a standalone, double-clickable macOS `.app` bundle:

```bash
chmod +x scripts/build_app.sh
./scripts/build_app.sh
```

The compiled application will be generated in `dist/FlacToAlac.app`.

---

## 🛠️ System Requirements

- **Python:** 3.9, 3.10, 3.11, or 3.12
- **FFmpeg:** Automatically discovered from system PATH, Homebrew (`/opt/homebrew/bin/ffmpeg`), or bundled fallback.

---

## 🧪 Running Tests

```bash
source .venv/bin/activate
QT_QPA_PLATFORM=offscreen python3 tests/test_converter.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
