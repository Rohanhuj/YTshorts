"""FFmpeg deterministic fixture renderer behind an injectable process boundary."""

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from shorts_automation.domain.errors import ErrorCode, ShortsAutomationError
from shorts_automation.domain.models import ContentArm, StructuredDraft
from shorts_automation.production.captions import CaptionStyle, write_ass


class CommandRunner(Protocol):
    def __call__(self, command: Sequence[str]) -> None: ...


def run_checked(command: Sequence[str]) -> None:
    subprocess.run(command, check=True, capture_output=True, text=True)


@dataclass(frozen=True)
class RenderSettings:
    width: int = 720
    height: int = 1280
    frames_per_second: int = 30
    safe_margin_pixels: int = 96
    font_name: str = "DejaVu Sans"


_ARM_COLORS = {
    ContentArm.FOOD: "#D35400",
    ContentArm.COOKING: "#117864",
    ContentArm.DOGS: "#5B2C6F",
}


def _subtitle_filter(path: Path) -> str:
    escaped = path.as_posix()
    for character in ("\\", ":", "'", "[", "]"):
        escaped = escaped.replace(character, f"\\{character}")
    return f"subtitles=filename='{escaped}'"


class FfmpegRenderer:
    """Render a non-black, silent 9:16 fixture without network or generated assets."""

    def __init__(self, runner: CommandRunner = run_checked, executable: str = "ffmpeg") -> None:
        self._runner = runner
        self._executable = executable

    def render_fixture(
        self, draft: StructuredDraft, output_path: Path, settings: RenderSettings | None = None
    ) -> Path:
        settings = settings or RenderSettings()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        captions_path = output_path.with_suffix(".ass")
        write_ass(
            draft,
            CaptionStyle(
                settings.width, settings.height, settings.safe_margin_pixels, settings.font_name
            ),
            captions_path,
        )
        command = [
            self._executable,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={_ARM_COLORS[draft.arm]}:s={settings.width}x{settings.height}:r={settings.frames_per_second}",
            "-t",
            f"{draft.target_duration_seconds:.3f}",
            "-vf",
            _subtitle_filter(captions_path),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(settings.frames_per_second),
            "-movflags",
            "+faststart",
            "-y",
            str(output_path),
        ]
        try:
            self._runner(command)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ShortsAutomationError(ErrorCode.RENDER_FAILED, "FFmpeg render failed") from exc
        return output_path
