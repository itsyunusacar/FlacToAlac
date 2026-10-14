# 🎵 FlacToAlac

> **Modern, Lossless FLAC to ALAC (Apple Lossless M4A) Audio Converter with Drag & Drop.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Platform: macOS | Windows | Linux](https://img.shields.io/badge/Platform-macOS%20|%20Windows%20|%20Linux-lightgrey.svg)]()
[![Code: Lossless](https://img.shields.io/badge/Audio-100%25%20Bit--Perfect%20Lossless-orange.svg)]()

---

## 🇹🇷 Türkçe Açıklama

**FlacToAlac**, FLAC formatındaki müzik arşivinizi Apple ekosisteminde (Apple Music, iTunes, iPhone, Mac, iPod) kayıpsız dinleyebilmeniz için **ALAC (.m4a)** formatına dönüştüren açık kaynaklı ve modern bir masaüstü uygulamasıdır.

### ✨ Öne Çıkan Özellikler
* **Sürükle ve Bırak (Drag & Drop):** Dosyaları veya tüm müzik klasörlerini pencereye sürüklemeniz yeterli.
* **%100 Kayıpsız Dönüşüm:** FLAC'ten ALAC'a geçerken ses kalitesinde en ufak bir sıkıştırma veya kalite kaybı yaşanmaz.
* **Albüm Kapağı & Metadata Koruması:** Şarkı adı, sanatçı, albüm, parça sırası ve yüksek çözünürlüklü gömülü albüm kapakları aynen aktarılır.
* **Hızlı Paralel Dönüştürme:** Çok çekirdekli (multi-thread) işlemci desteği sayesinde tüm albümler saniyeler içinde dönüştürülür.
* **Akıllı Çıktı Seçenekleri:** Orijinal dosyanın yanına veya seçeceğiniz özel bir klasöre (klasör hiyerarşisini koruyarak) çıktı alabilirsiniz.
* **Güvenli Silme Opsiyonu:** İsteğe bağlı olarak dönüştürme %100 doğrulandıktan sonra orijinal `.flac` dosyasını otomatik silebilir.
* **Kurulum Zahmetsiz:** Sistemde FFmpeg olmasa bile yerleşik motoruyla hemen çalışır.

### 🚀 Hızlı Başlangıç (macOS)
Terminali açıp proje klasöründe şu komutu çalıştırmanız yeterlidir:
```bash
./run.sh
```
*(Bu betik gereken sanal ortamı otomatik kurar ve uygulamayı başlatır.)*

Veya manuel olarak:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## 🇬🇧 English Description

**FlacToAlac** is a lightweight, open-source desktop application designed to batch convert FLAC audio files into ALAC (Apple Lossless Audio Codec in `.m4a` container) with an intuitive drag-and-drop interface.

### ✨ Key Features
* **Intuitive Drag & Drop:** Drop individual `.flac` files or entire album folders directly onto the app.
* **Zero Quality Loss:** Converts directly from FLAC to ALAC bit-for-bit losslessly.
* **Full Metadata & Artwork Retention:** Preserves tags (Title, Artist, Album, Year, Track #) and embedded high-res cover art.
* **Multi-threaded Batch Processing:** Uses configurable worker threads to convert entire discographies rapidly.
* **Flexible Destination:** Save converted `.m4a` files alongside originals or into a separate directory while preserving folder structures.
* **Safe Source Deletion (Optional):** Safely deletes source FLAC files only after the destination file has been verified.
* **Zero Configuration:** Bundles an automated FFmpeg fallback so you don't need manual setup.

---

## 🛠️ Requirements

* **Python:** 3.9 or higher
* **FFmpeg:** Automatically detected from system PATH, Homebrew, or bundled `imageio-ffmpeg`.

---

## 📦 Standalone App (.app / .dmg) Build

If you want to package this into a standalone macOS `.app`:
```bash
pip install pyinstaller
pyinstaller --name "FlacToAlac" --windowed --noconfirm --clean main.py
```
The resulting `.app` will be created inside the `dist/` directory.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
