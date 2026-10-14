import os
import sys
import shutil
import tempfile
import subprocess

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flactoalac.utils import get_ffmpeg_path, scan_paths_for_flac
from flactoalac.converter import ConversionTask, convert_single_file

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

        print("End-to-end conversion test passed with success!")

if __name__ == "__main__":
    test_conversion_end_to_end()
