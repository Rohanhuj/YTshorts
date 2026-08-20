import shutil
from pathlib import Path
from uuid import UUID

import pytest

from shorts_automation.domain.models import ContentArm, ContentFormat
from shorts_automation.production.renderer import FfmpegRenderer
from shorts_automation.production.validator import FfprobeValidator
from shorts_automation.providers.interfaces import DraftRequest
from shorts_automation.providers.mocks import MockTextProvider

FORMATS = {
    ContentArm.FOOD: ContentFormat.PICK_ONE,
    ContentArm.COOKING: ContentFormat.THREE_INGREDIENT_CHALLENGE,
    ContentArm.DOGS: ContentFormat.DOG_HAS_ONE_JOB,
}


@pytest.mark.parametrize("arm", list(ContentArm))
def test_fixture_short_renders_and_validates_for_every_arm(arm: ContentArm, tmp_path: Path) -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("FFmpeg and FFprobe are required for media integration tests")
    draft = MockTextProvider().generate_draft(
        DraftRequest(
            video_id=UUID(int=list(ContentArm).index(arm) + 1),
            arm=arm,
            format=FORMATS[arm],
            topic=f"fixture {arm.value}",
            deterministic_seed=0,
        )
    )
    output = FfmpegRenderer().render_fixture(draft, tmp_path / f"{arm.value.lower()}.mp4")

    result = FfprobeValidator().validate(output)

    assert result.duration_seconds == pytest.approx(24, abs=0.05)
    assert result.frame_count == 720
    assert output.stat().st_size > 0
