"""Perform a deterministic one-second FFmpeg/FFprobe CI smoke check."""

import json
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="shorts-ci-") as temp_dir:
        output = Path(temp_dir) / "smoke.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=720x1280:rate=30",
                "-t",
                "1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-y",
                str(output),
            ],
            check=True,
        )
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_name,width,height,pix_fmt",
                "-of",
                "json",
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        stream = json.loads(probe.stdout)["streams"][0]
        expected = {"codec_name": "h264", "width": 720, "height": 1280, "pix_fmt": "yuv420p"}
        if any(stream.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"unexpected FFprobe output: {stream}")
    print("FFmpeg smoke render passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
