import os
import sys
import shutil
import tempfile
import subprocess
import time

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QCoreApplication
from flactoalac.utils import get_ffmpeg_path, scan_paths_for_flac, open_path_in_file_manager
from flactoalac.converter import ConversionTask, convert_single_file, BatchConverterWorker

def test_conversion_end_to_end():
    ffmpeg = get_ffmpeg_path()
    assert ffmpeg is not None, "FFmpeg should be detected"

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a dummy test FLAC with metadata
        flac_path = os.path.join(tmpdir, "sample.flac")
        cmd = [
            ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-metadata", "title=EndToEnd Song",
            "-metadata", "artist=Test Artist",
            flac_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert os.path.exists(flac_path)

        # 2. Test scanning
        scanned = scan_paths_for_flac([tmpdir])
        assert len(scanned) == 1
        assert scanned[0]["filename"] == "sample.flac"

        # 3. Test conversion to ALAC (.m4a)
        m4a_path = os.path.join(tmpdir, "sample.m4a")
        task = ConversionTask(index=0, source_path=flac_path, dest_path=m4a_path, delete_source=False)
        success, msg = convert_single_file(task, ffmpeg)

        assert success is True, f"Conversion failed: {msg}"
        assert os.path.exists(m4a_path), "Destination file should exist"
        assert os.path.getsize(m4a_path) > 1024, "Destination file should have valid size"

        # 4. Test skip_existing
        task_skip = ConversionTask(index=0, source_path=flac_path, dest_path=m4a_path, delete_source=False, skip_existing=True)
        skip_success, skip_msg = convert_single_file(task_skip, ffmpeg)
        assert skip_success is True
        assert "Atlandı" in skip_msg

        print("End-to-end conversion & skip_existing tests passed with success!")

def test_worker_cancellation():
    app = QCoreApplication([])
    ffmpeg = get_ffmpeg_path()

    with tempfile.TemporaryDirectory() as tmpdir:
        tasks = []
        for i in range(5):
            flac_path = os.path.join(tmpdir, f"sample_{i}.flac")
            cmd = [
                ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                flac_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            m4a_path = os.path.join(tmpdir, f"sample_{i}.m4a")
            tasks.append(ConversionTask(index=i, source_path=flac_path, dest_path=m4a_path))

        worker = BatchConverterWorker(tasks, ffmpeg, max_workers=1)
        worker.start()
        time.sleep(0.05)
        worker.cancel()
        worker.wait(5000)

        assert worker.isFinished(), "Worker should finish cleanly after cancellation"
        print("Worker cancellation test passed with success!")

if __name__ == "__main__":
    test_conversion_end_to_end()
    test_worker_cancellation()
