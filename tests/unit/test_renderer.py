import subprocess
from pathlib import Path
from uuid import UUID

import pytest

from shorts_automation.domain.errors import ErrorCode, ShortsAutomationError
from shorts_automation.domain.models import ContentArm, ContentFormat, StructuredDraft
from shorts_automation.production.renderer import FfmpegRenderer
from shorts_automation.providers.interfaces import DraftRequest
from shorts_automation.providers.mocks import MockTextProvider


def _draft() -> StructuredDraft:
    return MockTextProvider().generate_draft(
        DraftRequest(
            video_id=UUID(int=2),
            arm=ContentArm.DOGS,
            format=ContentFormat.DOG_HAS_ONE_JOB,
            topic="fixture dog",
            deterministic_seed=0,
        )
    )


def test_renderer_builds_safe_deterministic_ffmpeg_command(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    renderer = FfmpegRenderer(runner=lambda command: commands.append(list(command)))

    output = renderer.render_fixture(_draft(), tmp_path / "path with spaces" / "[dog].mp4")

    assert output == tmp_path / "path with spaces" / "[dog].mp4"
    command = commands[0]
    assert [
        command[command.index(flag) + 1] for flag in ("-c:v", "-pix_fmt", "-r", "-movflags")
    ] == ["libx264", "yuv420p", "30", "+faststart"]
    assert "subtitles=filename='" in command[command.index("-vf") + 1]
    assert r"\[dog\].ass" in command[command.index("-vf") + 1]
    assert output.with_suffix(".ass").exists()


def test_renderer_normalizes_process_failure(tmp_path: Path) -> None:
    def fail(_command):  # type: ignore[no-untyped-def]
        raise subprocess.CalledProcessError(1, "ffmpeg")

    with pytest.raises(ShortsAutomationError) as exc_info:
        FfmpegRenderer(runner=fail).render_fixture(_draft(), tmp_path / "failed.mp4")
    assert exc_info.value.code is ErrorCode.RENDER_FAILED
