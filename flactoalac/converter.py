import os
import subprocess
import threading
from dataclasses import dataclass
from typing import Tuple, Optional, Callable, Set
from PyQt6.QtCore import QThread, pyqtSignal

@dataclass
class ConversionTask:
    index: int
    source_path: str
    dest_path: str
    delete_source: bool = False
    skip_existing: bool = False
    custom_cover_path: Optional[str] = None

def convert_single_file(
    task: ConversionTask,
    ffmpeg_path: str,
    on_proc_started: Optional[Callable[[subprocess.Popen], None]] = None,
    on_proc_ended: Optional[Callable[[subprocess.Popen], None]] = None,
    is_cancelled_fn: Optional[Callable[[], bool]] = None
) -> Tuple[bool, str]:
    """
    Converts a single FLAC file to ALAC M4A using FFmpeg.
    Preserves all audio streams, metadata, and embedded cover art.
    """
    if is_cancelled_fn and is_cancelled_fn():
        return False, "İşlem iptal edildi."

    if not os.path.isfile(task.source_path):
        return False, "Kaynak dosya bulunamadı."

    # Skip existing if enabled
    if task.skip_existing and os.path.exists(task.dest_path) and os.path.getsize(task.dest_path) > 1024:
        return True, "Zaten mevcut (Atlandı)."

    # Ensure destination directory exists
    os.makedirs(os.path.dirname(task.dest_path), exist_ok=True)

    def execute_ffmpeg(cmd_args: list[str]) -> Tuple[int, str]:
        proc = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if on_proc_started:
            on_proc_started(proc)
        try:
            _, stderr = proc.communicate(timeout=300)
            return proc.returncode, stderr
        except subprocess.TimeoutExpired:
            proc.kill()
            return -1, "İşlem zaman aşımına uğradı (5 dk)."
        finally:
            if on_proc_ended:
                on_proc_ended(proc)

    # Primary command: Map all streams (audio + embedded artwork + tags)
    primary_cmd = [
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

    ret_code, stderr = execute_ffmpeg(primary_cmd)

    if is_cancelled_fn and is_cancelled_fn():
        # Remove partial output on cancellation
        if os.path.exists(task.dest_path):
            try:
                os.remove(task.dest_path)
            except OSError:
                pass
        return False, "Kullanıcı tarafından iptal edildi."

    # Fallback attempt if stream mapping failed
    if ret_code != 0:
        fallback_cmd = [
            ffmpeg_path,
            "-y",
            "-nostdin",
            "-i", task.source_path,
            "-map_metadata", "0",
            "-c:a", "alac",
            task.dest_path
        ]
        ret_code, stderr = execute_ffmpeg(fallback_cmd)

    if is_cancelled_fn and is_cancelled_fn():
        if os.path.exists(task.dest_path):
            try:
                os.remove(task.dest_path)
            except OSError:
                pass
        return False, "Kullanıcı tarafından iptal edildi."

    if ret_code != 0:
        err_msg = stderr.strip() if stderr else "Bilinmeyen FFmpeg hatası."
        return False, f"FFmpeg Hatası:\n{err_msg}"

    # Verify output file
    if not os.path.exists(task.dest_path) or os.path.getsize(task.dest_path) < 1024:
        return False, "Çıktı dosyası geçersiz veya boş oluşturuldu."

    # Embed custom cover art if provided
    if task.custom_cover_path and os.path.isfile(task.custom_cover_path):
        from flactoalac.utils import embed_cover_art_to_m4a
        embed_cover_art_to_m4a(task.dest_path, task.custom_cover_path)

    # Delete source if requested and conversion was verified successful
    if task.delete_source:
        try:
            os.remove(task.source_path)
        except OSError as e:
            return True, f"Tamamlandı (Orijinal silinemedi: {e})"

    return True, "Başarıyla dönüştürüldü."


class BatchConverterWorker(QThread):
    """
    Background worker thread to process conversion tasks concurrently.
    Supports real-time per-task progress, thread safety, speed/ETA estimation, and instant cancellation.
    """
    task_started = pyqtSignal(int)                         # index
    task_finished = pyqtSignal(int, bool, str)             # index, success, message
    overall_progress = pyqtSignal(int, int, str)           # completed, total, stats_str (speed/ETA)
    all_finished = pyqtSignal(int, int, list)              # success_count, error_count, successful_dest_paths

    def __init__(self, tasks: list[ConversionTask], ffmpeg_path: str, max_workers: int = 4):
        super().__init__()
        self.tasks = tasks
        self.ffmpeg_path = ffmpeg_path
        self.max_workers = max_workers
        self._is_cancelled = False
        self._active_procs: Set[subprocess.Popen] = set()
        self._lock = threading.Lock()

    def cancel(self):
        self._is_cancelled = True
        with self._lock:
            for proc in list(self._active_procs):
                try:
                    proc.kill()
                except Exception:
                    pass
            self._active_procs.clear()

    def _on_proc_started(self, proc: subprocess.Popen):
        with self._lock:
            if self._is_cancelled:
                try:
                    proc.kill()
                except Exception:
                    pass
            else:
                self._active_procs.add(proc)

    def _on_proc_ended(self, proc: subprocess.Popen):
        with self._lock:
            self._active_procs.discard(proc)

    def _is_cancelled_check(self) -> bool:
        return self._is_cancelled

    def _run_single_task(self, task: ConversionTask) -> Tuple[int, bool, str, str]:
        if self._is_cancelled:
            return task.index, False, "İptal edildi.", task.dest_path

        # Emit task_started only when the worker thread is ACTUALLY starting it
        self.task_started.emit(task.index)

        success, msg = convert_single_file(
            task,
            self.ffmpeg_path,
            on_proc_started=self._on_proc_started,
            on_proc_ended=self._on_proc_ended,
            is_cancelled_fn=self._is_cancelled_check
        )
        return task.index, success, msg, task.dest_path

    def run(self):
        import concurrent.futures
        import time

        total = len(self.tasks)
        completed = 0
        success_count = 0
        error_count = 0
        successful_paths = []
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}
            for task in self.tasks:
                if self._is_cancelled:
                    break
                future = executor.submit(self._run_single_task, task)
                future_to_task[future] = task

            for future in concurrent.futures.as_completed(future_to_task):
                try:
                    task_index, success, message, dest_path = future.result()
                except Exception as exc:
                    task = future_to_task[future]
                    task_index, success, message, dest_path = task.index, False, str(exc), task.dest_path

                if success:
                    success_count += 1
                    successful_paths.append(dest_path)
                else:
                    error_count += 1

                self.task_finished.emit(task_index, success, message)
                completed += 1

                # Calculate speed and ETA
                elapsed = time.time() - start_time
                if elapsed > 0.3 and completed > 0:
                    speed = completed / elapsed
                    remaining_items = total - completed
                    if speed > 0 and remaining_items > 0:
                        eta_sec = remaining_items / speed
                        if eta_sec < 60:
                            eta_str = f"Kalan: ~{eta_sec:.0f} sn"
                        else:
                            eta_str = f"Kalan: ~{eta_sec / 60:.1f} dk"
                        stats_str = f"{speed:.1f} dosya/sn • {eta_str}"
                    else:
                        stats_str = f"{speed:.1f} dosya/sn"
                else:
                    stats_str = ""

                self.overall_progress.emit(completed, total, stats_str)

        self.all_finished.emit(success_count, error_count, successful_paths)

