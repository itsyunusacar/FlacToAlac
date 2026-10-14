import os
import sys
import subprocess
from typing import List, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFileDialog, QCheckBox, QRadioButton, QButtonGroup,
    QMessageBox, QFrame, QSpinBox, QAbstractItemView, QMenu,
    QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QColor, QFont, QIcon, QKeyEvent, QAction, QGuiApplication

from flactoalac.utils import (
    get_ffmpeg_path, format_size, scan_paths_for_flac, open_path_in_file_manager,
    add_to_apple_music
)
from flactoalac.converter import ConversionTask, BatchConverterWorker


class ErrorDetailDialog(QDialog):
    """Dialog to display full FFmpeg error logs with copy-to-clipboard support."""
    def __init__(self, filename: str, error_msg: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Hata Ayrıntısı - {filename}")
        self.resize(600, 360)
        self.setStyleSheet("""
            QDialog {
                background-color: #1C1C1E;
                color: #FFFFFF;
            }
            QTextEdit {
                background-color: #000000;
                color: #FF453A;
                font-family: Menlo, Monaco, "Courier New", monospace;
                font-size: 12px;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info_label = QLabel(f"<b>Dosya:</b> {filename}<br>Dönüştürme sırasında aşağıdaki hata oluştu:")
        info_label.setStyleSheet("color: #E5E5E7; font-size: 13px;")
        layout.addWidget(info_label)

        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setText(error_msg)
        layout.addWidget(self.text_box)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("Panoya Kopyala")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def copy_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.text_box.toPlainText())
            QMessageBox.information(self, "Kopyalandı", "Hata metni panoya kopyalandı.")


class DropZoneWidget(QFrame):
    """
    A modern drag-and-drop zone that accepts FLAC files and directories.
    """
    def __init__(self, on_paths_dropped, on_browse_clicked):
        super().__init__()
        self.on_paths_dropped = on_paths_dropped
        self.on_browse_clicked = on_browse_clicked
        self.setAcceptDrops(True)
        self.setObjectName("DropZone")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 24, 20, 24)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon / Emoji Label
        self.icon_label = QLabel("🎵")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        self.layout.addWidget(self.icon_label)

        # Main Text
        self.text_label = QLabel("FLAC Dosyalarını veya Klasörleri Buraya Sürükleyin")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #E5E5E7; background: transparent;")
        self.layout.addWidget(self.text_label)

        # Subtext / Browse button row
        sub_layout = QHBoxLayout()
        sub_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_layout.setSpacing(8)

        self.browse_files_btn = QPushButton("Dosya Seç")
        self.browse_files_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_files_btn.clicked.connect(lambda: self.on_browse_clicked(folder=False))
        self.browse_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
                border-color: #0A84FF;
            }
        """)

        self.browse_folders_btn = QPushButton("Klasör Seç")
        self.browse_folders_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_folders_btn.clicked.connect(lambda: self.on_browse_clicked(folder=True))
        self.browse_folders_btn.setStyleSheet(self.browse_files_btn.styleSheet())

        sub_layout.addWidget(self.browse_files_btn)
        sub_layout.addWidget(self.browse_folders_btn)
        self.layout.addLayout(sub_layout)

        self.set_idle_style()

    def set_idle_style(self):
        self.setStyleSheet("""
            QFrame#DropZone {
                border: 2px dashed #48484A;
                border-radius: 12px;
                background-color: #1C1C1E;
            }
        """)

    def set_active_style(self):
        self.setStyleSheet("""
            QFrame#DropZone {
                border: 2px dashed #0A84FF;
                border-radius: 12px;
                background-color: #162436;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.set_active_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.set_idle_style()

    def dropEvent(self, event: QDropEvent):
        self.set_idle_style()
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.on_paths_dropped(paths)


class MainWindow(QMainWindow):
    """
    Main application window for FlacToAlac.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flac to ALAC Converter")
        self.resize(880, 700)
        self.setMinimumSize(720, 520)

        # Allow full window drag-and-drop
        self.setAcceptDrops(True)

        self.ffmpeg_path = get_ffmpeg_path()
        self.file_items: List[Dict[str, any]] = []
        self.worker: BatchConverterWorker = None
        self.custom_dest_directory = ""
        self.custom_cover_path: Optional[str] = None

        # Window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()
        self.apply_dark_theme()

        # Check FFmpeg warning
        if not self.ffmpeg_path:
            QMessageBox.critical(
                self,
                "FFmpeg Bulunamadı",
                "Sisteminizde veya uygulama paketinde FFmpeg bulunamadı!\n"
                "Lütfen FFmpeg'i kurun (örn: brew install ffmpeg)."
            )

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Header Title and Subtitle
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_label = QLabel("Flac to ALAC Converter")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        subtitle_label = QLabel("Apple Lossless (ALAC / M4A) Dönüştürücü • Kayıpsız Ses & Kapak Görselleri")
        subtitle_label.setStyleSheet("font-size: 13px; color: #8E8E93;")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        ffmpeg_status = QLabel("🟢 FFmpeg Aktif" if self.ffmpeg_path else "🔴 FFmpeg Eksik")
        ffmpeg_status.setStyleSheet("font-size: 12px; font-weight: 500; color: #98989D;")
        header_layout.addWidget(ffmpeg_status)
        main_layout.addLayout(header_layout)

        # Drop Zone
        self.drop_zone = DropZoneWidget(
            on_paths_dropped=self.add_paths,
            on_browse_clicked=self.browse_paths
        )
        main_layout.addWidget(self.drop_zone)

        # Table Widget
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Dosya Adı", "Boyut", "Durum", "Hedef Yol"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 250)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        # Enable table drag-and-drop & context menu & double click
        self.table.setAcceptDrops(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.cellDoubleClicked.connect(self.on_table_double_clicked)
        main_layout.addWidget(self.table)

        # Options Box
        options_frame = QFrame()
        options_frame.setStyleSheet("""
            QFrame {
                background-color: #1C1C1E;
                border-radius: 8px;
                padding: 8px 10px;
            }
        """)
        options_layout = QVBoxLayout(options_frame)
        options_layout.setSpacing(8)

        # Destination Selection
        dest_layout = QHBoxLayout()
        dest_label = QLabel("Kayıt Konumu:")
        dest_label.setStyleSheet("font-weight: bold; color: #E5E5E7; font-size: 13px;")
        dest_layout.addWidget(dest_label)

        self.radio_same_dir = QRadioButton("Orijinal dosyanın yanına kaydet (.m4a)")
        self.radio_same_dir.setChecked(True)
        self.radio_same_dir.toggled.connect(self.update_dest_paths)
        dest_layout.addWidget(self.radio_same_dir)

        self.radio_custom_dir = QRadioButton("Özel klasöre kaydet:")
        self.radio_custom_dir.toggled.connect(self.update_dest_paths)
        dest_layout.addWidget(self.radio_custom_dir)

        self.custom_dest_btn = QPushButton("Klasör Seç...")
        self.custom_dest_btn.setEnabled(False)
        self.custom_dest_btn.clicked.connect(self.choose_custom_dest_dir)
        dest_layout.addWidget(self.custom_dest_btn)

        self.custom_dest_label = QLabel("")
        self.custom_dest_label.setStyleSheet("color: #0A84FF; font-size: 12px;")
        dest_layout.addWidget(self.custom_dest_label)
        dest_layout.addStretch()
        options_layout.addLayout(dest_layout)

        # Album Art Selection Row
        cover_layout = QHBoxLayout()
        cover_layout.setSpacing(10)

        self.cover_preview_label = QLabel("🖼️")
        self.cover_preview_label.setFixedSize(40, 40)
        self.cover_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview_label.setStyleSheet("""
            QLabel {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                font-size: 18px;
            }
        """)
        cover_layout.addWidget(self.cover_preview_label)

        cover_text_box = QVBoxLayout()
        cover_text_box.setSpacing(2)
        self.cover_title_label = QLabel("Albüm Kapağı (Opsiyonel):")
        self.cover_title_label.setStyleSheet("font-weight: bold; color: #E5E5E7; font-size: 13px;")
        self.cover_desc_label = QLabel("Orijinal gömülü kapak korunur • Görsel seçebilir veya sürükleyebilirsiniz")
        self.cover_desc_label.setStyleSheet("color: #8E8E93; font-size: 11px;")
        cover_text_box.addWidget(self.cover_title_label)
        cover_text_box.addWidget(self.cover_desc_label)
        cover_layout.addLayout(cover_text_box)

        self.choose_cover_btn = QPushButton("Kapak Seç...")
        self.choose_cover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.choose_cover_btn.clicked.connect(self.choose_custom_cover_file)
        self.choose_cover_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
                border-color: #0A84FF;
            }
        """)
        cover_layout.addWidget(self.choose_cover_btn)

        self.remove_cover_btn = QPushButton("✕ Kaldır")
        self.remove_cover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_cover_btn.setVisible(False)
        self.remove_cover_btn.clicked.connect(self.remove_custom_cover)
        self.remove_cover_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FF453A;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
        """)
        cover_layout.addWidget(self.remove_cover_btn)
        cover_layout.addStretch()
        options_layout.addLayout(cover_layout)

        # Checkboxes row
        checks_layout = QHBoxLayout()

        self.skip_existing_chk = QCheckBox("Zaten dönüştürülmüşleri atla")
        self.skip_existing_chk.setChecked(True)
        self.skip_existing_chk.setToolTip("Hedef konumda geçerli bir .m4a dosyası varsa tekrar dönüştürmez.")
        checks_layout.addWidget(self.skip_existing_chk)

        checks_layout.addSpacing(16)
        self.delete_source_chk = QCheckBox("Orijinal FLAC dosyasını sil")
        self.delete_source_chk.setStyleSheet("color: #FF453A; font-weight: 500;")
        self.delete_source_chk.setToolTip("Dönüştürme %100 başarılı olursa orijinal FLAC silinir.")
        checks_layout.addWidget(self.delete_source_chk)

        if sys.platform == "darwin":
            checks_layout.addSpacing(16)
            self.apple_music_chk = QCheckBox("Apple Music'e aktar")
            self.apple_music_chk.setChecked(False)
            self.apple_music_chk.setToolTip("Dönüştürülen parçaları otomatik olarak Apple Music kütüphanenize ekler.")
            checks_layout.addWidget(self.apple_music_chk)

        checks_layout.addSpacing(20)
        workers_label = QLabel("Eşzamanlı İşlem:")
        workers_label.setStyleSheet("color: #E5E5E7; font-size: 13px;")
        checks_layout.addWidget(workers_label)

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(min(os.cpu_count() or 4, 8))
        self.workers_spin.setFixedWidth(55)
        checks_layout.addWidget(self.workers_spin)

        checks_layout.addStretch()
        options_layout.addLayout(checks_layout)
        main_layout.addWidget(options_frame)

        # Bottom Bar: Stats, Progress Bar, Buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.stats_label = QLabel("Liste boş")
        self.stats_label.setStyleSheet("color: #8E8E93; font-size: 13px;")
        bottom_layout.addWidget(self.stats_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3A3A3C;
                border-radius: 5px;
                background-color: #2C2C2E;
                color: #FFFFFF;
                height: 18px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #30D158;
                border-radius: 4px;
            }
        """)
        bottom_layout.addWidget(self.progress_bar)

        self.open_output_btn = QPushButton("📁 Klasörü Aç")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        self.open_output_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_output_btn.setToolTip("Çıktı klasörünü Finder'da açar.")
        self.open_output_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 7px;
                padding: 8px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
                border-color: #0A84FF;
            }
        """)
        bottom_layout.addWidget(self.open_output_btn)

        self.clear_btn = QPushButton("Listeyi Temizle")
        self.clear_btn.clicked.connect(self.clear_list)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FF453A;
                border: 1px solid #3A3A3C;
                border-radius: 7px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
        """)
        bottom_layout.addWidget(self.clear_btn)

        self.start_btn = QPushButton("Dönüştürmeyi Başlat")
        self.start_btn.clicked.connect(self.toggle_conversion)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0071E3;
            }
            QPushButton:disabled {
                background-color: #3A3A3C;
                color: #8E8E93;
            }
        """)
        bottom_layout.addWidget(self.start_btn)
        main_layout.addLayout(bottom_layout)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                color: #FFFFFF;
                font-family: "system-ui", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
            }
            QTableWidget {
                background-color: #1C1C1E;
                border: 1px solid #2C2C2E;
                border-radius: 8px;
                gridline-color: #2C2C2E;
                selection-background-color: #0A84FF;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #252528;
            }
            QHeaderView::section {
                background-color: #252528;
                color: #8E8E93;
                padding: 6px;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QRadioButton, QCheckBox {
                spacing: 6px;
                font-size: 13px;
                color: #E5E5E7;
            }
            QSpinBox {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 4px;
                color: #FFFFFF;
                padding: 2px 4px;
            }
            QMenu {
                background-color: #252528;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0A84FF;
            }
        """)

    # --- Full Window Drag & Drop Handlers ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_zone.set_active_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_zone.set_idle_style()

    def dropEvent(self, event: QDropEvent):
        self.drop_zone.set_idle_style()
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.add_paths(paths)

    def choose_custom_cover_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Albüm Kapak Görselini Seçin",
            "",
            "Görsel Dosyaları (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        if file_path:
            self.set_custom_cover(file_path)

    def set_custom_cover(self, image_path: str):
        if not os.path.isfile(image_path):
            return
        self.custom_cover_path = image_path
        filename = os.path.basename(image_path)
        self.cover_title_label.setText(f"Özel Kapak: {filename}")
        self.cover_desc_label.setText("Tüm dönüştürülen parçalara bu kapak gömülecek")
        self.cover_desc_label.setStyleSheet("color: #30D158; font-size: 11px;")
        self.remove_cover_btn.setVisible(True)

        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                40, 40,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.cover_preview_label.setPixmap(scaled)
        else:
            self.cover_preview_label.setText("🖼️")

    def remove_custom_cover(self):
        self.custom_cover_path = None
        self.cover_preview_label.setText("🖼️")
        self.cover_title_label.setText("Albüm Kapağı (Opsiyonel):")
        self.cover_desc_label.setText("Orijinal gömülü kapak korunur • Görsel seçebilir veya sürükleyebilirsiniz")
        self.cover_desc_label.setStyleSheet("color: #8E8E93; font-size: 11px;")
        self.remove_cover_btn.setVisible(False)

    def browse_paths(self, folder: bool = False):
        if folder:
            dir_path = QFileDialog.getExistingDirectory(self, "FLAC İçeren Klasörü Seçin")
            if dir_path:
                self.add_paths([dir_path])
        else:
            files, _ = QFileDialog.getOpenFileNames(
                self, "FLAC Dosyalarını Seçin", "", "FLAC Audio (*.flac *.FLAC)"
            )
            if files:
                self.add_paths(files)

    def add_paths(self, paths: List[str]):
        # Separate images from audio/folders
        image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
        image_files = [p for p in paths if os.path.isfile(p) and p.lower().endswith(image_extensions)]
        audio_or_dirs = [p for p in paths if p not in image_files]

        if image_files:
            # Set the first image as custom cover
            self.set_custom_cover(image_files[0])

        if not audio_or_dirs and image_files:
            # Only images were dropped
            return

        new_items = scan_paths_for_flac(audio_or_dirs)
        if not new_items:
            if not image_files:
                QMessageBox.information(self, "Bilgi", "Seçilen konumda .flac dosyası bulunamadı.")
            return

        existing_paths = {item["path"] for item in self.file_items}
        added_count = 0

        for item in new_items:
            if item["path"] not in existing_paths:
                self.file_items.append(item)
                existing_paths.add(item["path"])
                added_count += 1

        self.refresh_table()

    def choose_custom_dest_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Çıktı Klasörünü Seçin")
        if dir_path:
            self.custom_dest_directory = dir_path
            self.custom_dest_label.setText(os.path.basename(dir_path))
            self.custom_dest_label.setToolTip(dir_path)
            self.update_dest_paths()

    def update_dest_paths(self):
        is_custom = self.radio_custom_dir.isChecked()
        self.custom_dest_btn.setEnabled(is_custom)

        for row, item in enumerate(self.file_items):
            dest_path = self.calculate_dest_path(item)
            item["dest_path"] = dest_path
            self.table.setItem(row, 3, QTableWidgetItem(dest_path))

    def calculate_dest_path(self, item: Dict[str, any]) -> str:
        base_name = os.path.splitext(item["filename"])[0] + ".m4a"

        if self.radio_same_dir.isChecked() or not self.custom_dest_directory:
            return os.path.join(item["dir"], base_name)
        else:
            rel_dir = os.path.relpath(item["dir"], item["base_dir"])
            if rel_dir and rel_dir != ".":
                return os.path.join(self.custom_dest_directory, rel_dir, base_name)
            return os.path.join(self.custom_dest_directory, base_name)

    def refresh_table(self):
        self.table.setRowCount(len(self.file_items))
        total_size = 0

        for row, item in enumerate(self.file_items):
            total_size += item.get("size", 0)

            # Name item
            name_item = QTableWidgetItem(item["filename"])
            name_item.setToolTip(item["path"])
            self.table.setItem(row, 0, name_item)

            # Size item
            size_item = QTableWidgetItem(format_size(item.get("size", 0)))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)

            # Status item
            status_str = item.get("status_str", "Hazır")
            status_item = QTableWidgetItem(status_str)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if "Tamamlandı" in status_str:
                status_item.setForeground(QColor("#30D158"))
            elif "Hata" in status_str:
                status_item.setForeground(QColor("#FF453A"))
            elif "Dönüştürülüyor" in status_str:
                status_item.setForeground(QColor("#0A84FF"))
            self.table.setItem(row, 2, status_item)

            # Destination item
            dest_path = self.calculate_dest_path(item)
            item["dest_path"] = dest_path
            dest_item = QTableWidgetItem(dest_path)
            dest_item.setToolTip(dest_path)
            self.table.setItem(row, 3, dest_item)

        self.stats_label.setText(
            f"Toplam {len(self.file_items)} dosya ({format_size(total_size)})"
            if self.file_items else "Liste boş"
        )

    # --- Item Removal & Keyboard Events ---
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_selected_rows()
        else:
            super().keyPressEvent(event)

    def remove_selected_rows(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Uyarı", "Dönüştürme sürerken listeden dosya silinemez.")
            return

        selected_rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            return

        for row in selected_rows:
            if 0 <= row < len(self.file_items):
                del self.file_items[row]

        self.refresh_table()

    # --- Context Menu ---
    def show_table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        menu = QMenu(self)

        remove_action = QAction("🗑️ Seçilenleri Listeden Kaldır", self)
        remove_action.triggered.connect(self.remove_selected_rows)
        menu.addAction(remove_action)

        if item:
            row = item.row()
            file_data = self.file_items[row] if row < len(self.file_items) else None

            menu.addSeparator()
            if file_data:
                open_source_action = QAction("📂 Kaynak Dosyayı Finder'da Göster", self)
                open_source_action.triggered.connect(lambda: open_path_in_file_manager(file_data["path"]))
                menu.addAction(open_source_action)

                if os.path.exists(file_data.get("dest_path", "")):
                    open_dest_action = QAction("📁 Hedef (.m4a) Dosyasını Finder'da Göster", self)
                    open_dest_action.triggered.connect(lambda: open_path_in_file_manager(file_data["dest_path"]))
                    menu.addAction(open_dest_action)

                if "error_details" in file_data:
                    error_action = QAction("⚠️ Hata Ayrıntısını Gör", self)
                    error_action.triggered.connect(lambda: self.show_error_dialog(file_data["filename"], file_data["error_details"]))
                    menu.addAction(error_action)

        menu.addSeparator()
        clear_action = QAction("🧹 Listeyi Temizle", self)
        clear_action.triggered.connect(self.clear_list)
        menu.addAction(clear_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def on_table_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.file_items):
            item = self.file_items[row]
            if "error_details" in item:
                self.show_error_dialog(item["filename"], item["error_details"])
            elif os.path.exists(item.get("dest_path", "")):
                open_path_in_file_manager(item["dest_path"])
            else:
                open_path_in_file_manager(item["path"])

    def show_error_dialog(self, filename: str, error_details: str):
        dlg = ErrorDetailDialog(filename, error_details, self)
        dlg.exec()

    def open_output_folder(self):
        """Opens output folder in Finder."""
        if self.radio_custom_dir.isChecked() and self.custom_dest_directory and os.path.exists(self.custom_dest_directory):
            open_path_in_file_manager(self.custom_dest_directory)
            return

        # Fallback to selected row's output or first file's output
        selected_rows = [idx.row() for idx in self.table.selectedIndexes()]
        target_row = selected_rows[0] if selected_rows else 0

        if 0 <= target_row < len(self.file_items):
            dest_path = self.file_items[target_row].get("dest_path", "")
            target_dir = os.path.dirname(dest_path) if dest_path else ""
            if os.path.exists(target_dir):
                open_path_in_file_manager(target_dir)
                return

        # Fallback to user's music folder
        music_dir = os.path.expanduser("~/Music")
        open_path_in_file_manager(music_dir)

    def clear_list(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Uyarı", "Dönüştürme işlemi sürerken liste temizlenemez.")
            return
        self.file_items.clear()
        self.table.setRowCount(0)
        self.stats_label.setText("Liste boş")
        self.progress_bar.setVisible(False)

    def toggle_conversion(self):
        if self.worker and self.worker.isRunning():
            # Cancel current run
            self.worker.cancel()
            self.start_btn.setEnabled(False)
            self.start_btn.setText("İptal ediliyor...")
            return

        if not self.ffmpeg_path:
            QMessageBox.critical(self, "Hata", "FFmpeg bulunamadığı için işlem başlatılamıyor.")
            return

        if not self.file_items:
            QMessageBox.information(self, "Uyarı", "Lütfen önce FLAC dosyası ekleyin.")
            return

        if self.radio_custom_dir.isChecked() and not self.custom_dest_directory:
            QMessageBox.warning(self, "Klasör Seçilmedi", "Lütfen dönüştürülen dosyaların kaydedileceği klasörü seçin.")
            return

        # Prepare tasks
        delete_source = self.delete_source_chk.isChecked()
        skip_existing = self.skip_existing_chk.isChecked()
        tasks = []

        for index, item in enumerate(self.file_items):
            task = ConversionTask(
                index=index,
                source_path=item["path"],
                dest_path=item["dest_path"],
                delete_source=delete_source,
                skip_existing=skip_existing,
                custom_cover_path=self.custom_cover_path
            )
            tasks.append(task)
            item["status_str"] = "Kuyrukta..."
            if "error_details" in item:
                del item["error_details"]
            self.table.item(index, 2).setText("Kuyrukta...")
            self.table.item(index, 2).setForeground(QColor("#8E8E93"))

        # Setup progress bar
        self.progress_bar.setMaximum(len(tasks))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Switch button state
        self.start_btn.setText("Dönüştürmeyi İptal Et")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF453A;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D70015;
            }
        """)
        self.clear_btn.setEnabled(False)

        # Launch worker
        max_workers = self.workers_spin.value()
        self.worker = BatchConverterWorker(tasks, self.ffmpeg_path, max_workers=max_workers)
        self.worker.task_started.connect(self.on_task_started)
        self.worker.task_finished.connect(self.on_task_finished)
        self.worker.overall_progress.connect(self.on_overall_progress)
        self.worker.all_finished.connect(self.on_all_finished)
        self.worker.start()

    def on_task_started(self, index: int):
        if 0 <= index < len(self.file_items):
            self.file_items[index]["status_str"] = "Dönüştürülüyor..."
            item = self.table.item(index, 2)
            if item:
                item.setText("⏳ Dönüştürülüyor")
                item.setForeground(QColor("#0A84FF"))

    def on_task_finished(self, index: int, success: bool, message: str):
        if not (0 <= index < len(self.file_items)):
            return
        item = self.table.item(index, 2)
        if not item:
            return

        if success:
            status_text = "✅ Atlandı" if "Atlandı" in message else "✅ Tamamlandı"
            self.file_items[index]["status_str"] = status_text
            item.setText(status_text)
            item.setForeground(QColor("#30D158"))
            item.setToolTip(message)
        else:
            self.file_items[index]["status_str"] = "Hata"
            self.file_items[index]["error_details"] = message
            item.setText("❌ Hata (Çift Tıkla)")
            item.setForeground(QColor("#FF453A"))
            item.setToolTip(message)

    def on_overall_progress(self, completed: int, total: int, stats_str: str = ""):
        self.progress_bar.setValue(completed)
        if stats_str:
            self.progress_bar.setFormat(f"%p% ({completed}/{total}) • {stats_str}")
        else:
            self.progress_bar.setFormat(f"%p% ({completed}/{total})")

    def on_all_finished(self, success_count: int, error_count: int, successful_paths: list = None):
        self.start_btn.setText("Dönüştürmeyi Başlat")
        self.start_btn.setEnabled(True)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0071E3;
            }
        """)
        self.clear_btn.setEnabled(True)

        added_music_count = 0
        if hasattr(self, 'apple_music_chk') and self.apple_music_chk.isChecked() and successful_paths:
            if add_to_apple_music(successful_paths):
                added_music_count = len(successful_paths)

        msg = f"Dönüştürme işlemi tamamlandı!\n\nBaşarılı: {success_count}\nHata: {error_count}"
        if added_music_count > 0:
            msg += f"\n\n🎵 {added_music_count} parça Apple Music'e aktarıldı."

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("İşlem Tamamlandı")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Icon.Information if error_count == 0 else QMessageBox.Icon.Warning)

        open_btn = msg_box.addButton("Klasörü Aç", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton("Tamam", QMessageBox.ButtonRole.AcceptRole)

        msg_box.exec()
        if msg_box.clickedButton() == open_btn:
            self.open_output_folder()
