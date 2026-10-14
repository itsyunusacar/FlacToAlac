#!/usr/bin/env python3
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from flactoalac.ui import MainWindow

def main():
    # macOS / High DPI support
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("FlacToAlac")
    app.setApplicationDisplayName("Flac to ALAC Converter")

    window = MainWindow()

    # Handle command-line arguments / files opened with app
    initial_paths = [
        arg for arg in sys.argv[1:]
        if not arg.startswith("-") and os.path.exists(arg)
    ]
    if initial_paths:
        window.add_paths(initial_paths)

    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
