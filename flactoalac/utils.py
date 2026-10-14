import os
import shutil
from typing import List, Dict, Optional

def get_ffmpeg_path() -> Optional[str]:
    """Finds a working ffmpeg executable on the system or in packages."""
    # 1. System PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 2. Common macOS / Linux paths
    common_paths = [
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/usr/bin/ffmpeg"
    ]
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    # 3. imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.isfile(bundled) and os.access(bundled, os.X_OK):
            return bundled
    except Exception:
        pass

    return None

def format_size(num_bytes: int) -> str:
    """Formats bytes into human readable format (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"

def scan_paths_for_flac(paths: List[str]) -> List[Dict[str, any]]:
    """
    Given a list of file and directory paths, recursively collects all .flac files.
    Returns a list of dicts with file metadata.
    """
    flac_files = []
    seen = set()

    for path in paths:
        path = os.path.abspath(path)
        if os.path.isfile(path):
            if path.lower().endswith('.flac') and path not in seen:
                seen.add(path)
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                flac_files.append({
                    "path": path,
                    "filename": os.path.basename(path),
                    "size": size,
                    "dir": os.path.dirname(path),
                    "base_dir": os.path.dirname(path)
                })
        elif os.path.isdir(path):
            base_dir = path
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.flac'):
                        full_path = os.path.join(root, file)
                        if full_path not in seen:
                            seen.add(full_path)
                            try:
                                size = os.path.getsize(full_path)
                            except OSError:
                                size = 0
                            flac_files.append({
                                "path": full_path,
                                "filename": file,
                                "size": size,
                                "dir": root,
                                "base_dir": base_dir
                            })

    return flac_files


def open_path_in_file_manager(path: str):
    """Opens a file or directory in macOS Finder, Windows Explorer, or Linux file manager."""
    import sys
    import subprocess

    if not path or not os.path.exists(path):
        return

    try:
        if sys.platform == "darwin":
            if os.path.isfile(path):
                subprocess.run(["open", "-R", path])
            else:
                subprocess.run(["open", path])
        elif sys.platform == "win32":
            if os.path.isfile(path):
                subprocess.run(["explorer", f"/select,{os.path.normpath(path)}"])
            else:
                subprocess.run(["explorer", os.path.normpath(path)])
        else:
            # Linux
            target = os.path.dirname(path) if os.path.isfile(path) else path
            subprocess.run(["xdg-open", target])
    except Exception:
        pass


def add_to_apple_music(paths: List[str]) -> bool:
    """
    Imports audio files into Apple Music library on macOS.
    Returns True if successfully triggered.
    """
    import sys
    import subprocess

    if sys.platform != "darwin" or not paths:
        return False

    valid_paths = [os.path.abspath(p) for p in paths if os.path.exists(p)]
    if not valid_paths:
        return False

    try:
        # Batch open with Apple Music
        subprocess.run(["open", "-a", "Music"] + valid_paths, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


