import os
import subprocess
from dataclasses import dataclass
from typing import Tuple, Optional
from PyQt6.QtCore import QThread, pyqtSignal

@dataclass
class ConversionTask:
    index: int
    source_path: str
    dest_path: str
    delete_source: bool = False

def convert_single_file(task: ConversionTask, ffmpeg_path: str) -> Tuple[bool, str]:
    """
    Converts a single FLAC file to ALAC M4A using FFmpeg.
    Ensures album art and metadata are preserved.
    """
    if not os.path.isfile(task.source_path):
        return False, "Kaynak dosya bulunamadı."

    # Ensure destination directory exists
    os.makedirs(os.path.dirname(task.dest_path), exist_ok=True)

    # Primary conversion command (preserves all streams: audio, cover art, tags)
    cmd = [
        ffmpeg_path,
        "-y",
        "-nostdin",
        "-i", task.source_path,
        "-map", "0",
        "-map_metadata", "0",
        "-c:v", "copy",
        "-c:a", "alac",
        task.dest_path
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )

        # Fallback if stream mapping failed (e.g., unsupported non-audio streams)
        if proc.returncode != 0:
            fallback_cmd = [
                ffmpeg_path,
                "-y",
                "-nostdin",
                "-i", task.source_path,
                "-map_metadata", "0",
                "-c:a", "alac",
                task.dest_path
            ]
            proc = subprocess.run(
                fallback_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

        if proc.returncode != 0:
            err_msg = proc.stderr.strip().split("\n")[-1] if proc.stderr else "Bilinmeyen FFmpeg hatası."
            return False, f"FFmpeg Hatası: {err_msg}"

        # Verify output file
        if not os.path.exists(task.dest_path) or os.path.getsize(task.dest_path) < 1024:
            return False, "Çıktı dosyası geçersiz veya boş oluşturuldu."

        # Delete source if requested and conversion was 100% successful
        if task.delete_source:
            try:
                os.remove(task.source_path)
            except OSError as e:
                return True, f"Tamamlandı (Orijinal silinemedi: {e})"

        return True, "Başarıyla dönüştürüldü."

    except subprocess.TimeoutExpired:
        return False, "İşlem zaman aşımına uğradı (5 dk)."
    except Exception as e:
        return False, f"Hata: {str(e)}"


class BatchConverterWorker(QThread):
    """
    Background worker thread to process conversion tasks without freezing the GUI.
    """
    task_started = pyqtSignal(int)                         # index
    task_finished = pyqtSignal(int, bool, str)             # index, success, message
    overall_progress = pyqtSignal(int, int)                # completed, total
    all_finished = pyqtSignal(int, int)                    # success_count, error_count

    def __init__(self, tasks: list[ConversionTask], ffmpeg_path: str, max_workers: int = 4):
        super().__init__()
        self.tasks = tasks
        self.ffmpeg_path = ffmpeg_path
        self.max_workers = max_workers
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        import concurrent.futures

        total = len(self.tasks)
        completed = 0
        success_count = 0
        error_count = 0

        # Execute tasks using thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}

            for task in self.tasks:
                if self._is_cancelled:
                    break
                self.task_started.emit(task.index)
                future = executor.submit(convert_single_file, task, self.ffmpeg_path)
                future_to_task[future] = task

            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                if self._is_cancelled:
                    self.task_finished.emit(task.index, False, "Kullanıcı tarafından iptal edildi.")
                    error_count += 1
                else:
                    try:
                        success, message = future.result()
                    except Exception as exc:
                        success, message = False, str(exc)

                    if success:
                        success_count += 1
                    else:
                        error_count += 1

                    self.task_finished.emit(task.index, success, message)

                completed += 1
                self.overall_progress.emit(completed, total)

        self.all_finished.emit(success_count, error_count)
