"""Strict FFprobe validation for rendered Shorts."""

import json
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from shorts_automation.domain.errors import ErrorCode, ShortsAutomationError

ProbeRunner = Callable[[Sequence[str]], str]


def run_probe(command: Sequence[str]) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def run_frame_probe(command: Sequence[str]) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


@dataclass(frozen=True)
class MediaValidation:
    duration_seconds: float
    width: int
    height: int
    frames_per_second: float
    frame_count: int
    file_size_bytes: int
    has_audio: bool


class FfprobeValidator:
    def __init__(
        self,
        runner: ProbeRunner = run_probe,
        frame_runner: ProbeRunner | None = None,
        executable: str = "ffprobe",
        frame_executable: str = "ffmpeg",
    ) -> None:
        self._runner = runner
        self._frame_runner = frame_runner or run_frame_probe
        self._executable = executable
        self._frame_executable = frame_executable

    def validate(self, media_path: Path, *, audio_expected: bool = False) -> MediaValidation:
        command = [
            self._executable,
            "-v",
            "error",
            "-count_frames",
            "-show_entries",
            "format=format_name,duration,size:stream=codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,nb_read_frames",
            "-of",
            "json",
            str(media_path),
        ]
        try:
            payload: dict[str, Any] = json.loads(self._runner(command))
            result = self._validate_payload(payload, audio_expected=audio_expected)
            self._validate_first_frame(media_path)
            return result
        except ShortsAutomationError:
            raise
        except (
            OSError,
            subprocess.CalledProcessError,
            AttributeError,
            ValueError,
            KeyError,
            TypeError,
            ZeroDivisionError,
            OverflowError,
        ) as exc:
            raise ShortsAutomationError(
                ErrorCode.VALIDATION_FAILED, "FFprobe could not inspect rendered media"
            ) from exc

    def _validate_first_frame(self, media_path: Path) -> None:
        command = [
            self._frame_executable,
            "-v",
            "error",
            "-i",
            str(media_path),
            "-frames:v",
            "1",
            "-vf",
            "signalstats,metadata=print:file=-",
            "-f",
            "null",
            "-",
        ]
        output = self._frame_runner(command)
        average_line = next(
            (line for line in output.splitlines() if "lavfi.signalstats.YAVG=" in line), None
        )
        if average_line is None:
            raise ShortsAutomationError(
                ErrorCode.VALIDATION_FAILED, "first-frame luminance was not reported"
            )
        luminance = float(average_line.rsplit("=", maxsplit=1)[1])
        if not 16 < luminance <= 255:
            raise ShortsAutomationError(
                ErrorCode.VALIDATION_FAILED, "first frame is black or empty"
            )

    @staticmethod
    def _validate_payload(payload: dict[str, Any], *, audio_expected: bool) -> MediaValidation:
        streams = payload["streams"]
        videos = [stream for stream in streams if stream.get("codec_type") == "video"]
        audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
        if len(videos) != 1:
            raise ShortsAutomationError(ErrorCode.VALIDATION_FAILED, "expected one video stream")
        video = videos[0]
        media_format = payload["format"]
        duration = float(media_format["duration"])
        width, height = int(video["width"]), int(video["height"])
        fps = float(Fraction(video["avg_frame_rate"]))
        frames, size = int(video["nb_read_frames"]), int(media_format["size"])
        checks = {
            "container must be MP4": "mp4" in media_format.get("format_name", ""),
            "duration must be between 15 and 35 seconds": 15 <= duration <= 35,
            "video codec must be H.264": video.get("codec_name") == "h264",
            "pixel format must be yuv420p": video.get("pix_fmt") == "yuv420p",
            "dimensions must be 720x1280 or 1080x1920": (width, height)
            in {(720, 1280), (1080, 1920)},
            "display aspect ratio must be 9:16": width * 16 == height * 9,
            "frame rate must be 30 fps": abs(fps - 30) < 0.01,
            "frame count must match duration": abs(frames - round(duration * fps)) <= 1,
            "file must not be empty": size > 0,
            "audio presence does not match expectation": bool(audios) is audio_expected,
            "audio codec must be AAC": not audios
            or all(a.get("codec_name") == "aac" for a in audios),
        }
        failures = [message for message, passed in checks.items() if not passed]
        if failures:
            raise ShortsAutomationError(ErrorCode.VALIDATION_FAILED, "; ".join(failures))
        return MediaValidation(duration, width, height, fps, frames, size, bool(audios))
