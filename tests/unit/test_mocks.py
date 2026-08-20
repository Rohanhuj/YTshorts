from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from shorts_automation.providers.interfaces import (
    ImageRequest,
    UploadRequest,
    VideoRequest,
)
from shorts_automation.providers.mocks import (
    MockFactProvider,
    MockPublishingProvider,
    MockVisualProvider,
)


def test_mock_asset_is_deterministic_and_free() -> None:
    request = ImageRequest(
        video_id=UUID(int=1),
        scene_number=1,
        prompt="A sufficiently detailed mock image prompt",
        idempotency_key="video-1:scene-1:image:v1",
    )
    provider = MockVisualProvider()

    first = provider.generate_image(request)
    second = provider.generate_image(request)

    assert first == second
    assert first.actual_cost_usd == 0
    assert len(first.sha256) == 64


def test_mock_publishing_upload_is_always_private_and_deterministic() -> None:
    request = UploadRequest(
        video_id=UUID(int=1),
        file_path=Path("fixture.mp4"),
        artifact_sha256="a" * 64,
        title="Fixture",
        description="Safe deterministic fixture",
        made_for_kids=False,
        contains_synthetic_media=True,
        idempotency_key="upload:fixture:v1",
    )
    provider = MockPublishingProvider()

    first = provider.upload_private(request)
    second = provider.upload_private(request)

    assert first == second
    assert first.privacy_status == "private"


def test_mock_publishing_schedule_requires_future_aware_time() -> None:
    provider = MockPublishingProvider()
    publish_at = datetime.now(UTC) + timedelta(days=1)

    provider.schedule("mock-video", publish_at)

    assert provider.scheduled["mock-video"] == publish_at


def test_mock_video_and_fact_providers_are_zero_network_fixtures() -> None:
    video = MockVisualProvider().generate_video(
        VideoRequest(
            video_id=UUID(int=2),
            scene_number=1,
            prompt="A sufficiently detailed mock video prompt",
            duration_seconds=4,
            idempotency_key="video-2:scene-1:video:v1",
        )
    )
    facts = MockFactProvider().search("protein comparison")

    assert video.media_type == "mp4"
    assert video.actual_cost_usd == 0
    assert facts[0].source_id == "fixture-fdc-001"


@pytest.mark.parametrize(
    "publish_at",
    [datetime(2026, 8, 20, 12, 0), datetime.now(UTC) - timedelta(seconds=1)],
)
def test_mock_schedule_rejects_naive_or_past_time(publish_at: datetime) -> None:
    with pytest.raises(ValueError, match="future"):
        MockPublishingProvider().schedule("mock-video", publish_at)
