from uuid import UUID

import pytest
from pydantic import ValidationError

from shorts_automation.domain.models import ContentArm, ContentFormat, StructuredDraft
from shorts_automation.providers.interfaces import DraftRequest
from shorts_automation.providers.mocks import MockTextProvider


@pytest.mark.parametrize(
    ("arm", "content_format"),
    [
        (ContentArm.FOOD, ContentFormat.PICK_ONE),
        (ContentArm.COOKING, ContentFormat.THREE_INGREDIENT_CHALLENGE),
        (ContentArm.DOGS, ContentFormat.DOG_HAS_ONE_JOB),
    ],
)
def test_mock_draft_validates_for_every_arm(arm: ContentArm, content_format: ContentFormat) -> None:
    request = DraftRequest(
        video_id=UUID(int=list(ContentArm).index(arm) + 1),
        arm=arm,
        format=content_format,
        topic=f"fixture {arm.value}",
        deterministic_seed=7,
    )

    draft = MockTextProvider().generate_draft(request)

    assert draft.arm is arm
    assert sum(scene.duration_seconds for scene in draft.scenes) == draft.target_duration_seconds
    assert StructuredDraft.model_validate_json(draft.model_dump_json()) == draft


def test_food_draft_without_facts_fails_closed() -> None:
    request = DraftRequest(
        video_id=UUID(int=10),
        arm=ContentArm.FOOD,
        format=ContentFormat.PICK_ONE,
        topic="breakfast comparison",
        deterministic_seed=0,
    )
    valid = MockTextProvider().generate_draft(request)

    with pytest.raises(ValidationError, match="require approved factual citations"):
        StructuredDraft.model_validate({**valid.model_dump(), "facts": []})


def test_cross_arm_format_is_rejected() -> None:
    request = DraftRequest(
        video_id=UUID(int=11),
        arm=ContentArm.DOGS,
        format=ContentFormat.DOG_HAS_ONE_JOB,
        topic="office dog",
        deterministic_seed=0,
    )
    valid = MockTextProvider().generate_draft(request)

    with pytest.raises(ValidationError, match="is not allowed for arm"):
        StructuredDraft.model_validate({**valid.model_dump(), "format": "PICK_ONE"})


def test_scene_duration_must_match_target() -> None:
    request = DraftRequest(
        video_id=UUID(int=12),
        arm=ContentArm.DOGS,
        format=ContentFormat.DOG_HAS_ONE_JOB,
        topic="office dog",
        deterministic_seed=0,
    )
    valid = MockTextProvider().generate_draft(request)

    with pytest.raises(ValidationError, match="must sum"):
        StructuredDraft.model_validate({**valid.model_dump(), "target_duration_seconds": 25})


def test_scene_numbers_must_be_sequential() -> None:
    request = DraftRequest(
        video_id=UUID(int=13),
        arm=ContentArm.DOGS,
        format=ContentFormat.DOG_HAS_ONE_JOB,
        topic="office dog",
        deterministic_seed=0,
    )
    valid = MockTextProvider().generate_draft(request)
    scenes = [scene.model_dump() for scene in valid.scenes]
    scenes[1]["scene_number"] = 3

    with pytest.raises(ValidationError, match="must be sequential"):
        StructuredDraft.model_validate({**valid.model_dump(), "scenes": scenes})


def test_visual_budget_rejects_more_than_one_video() -> None:
    request = DraftRequest(
        video_id=UUID(int=14),
        arm=ContentArm.DOGS,
        format=ContentFormat.DOG_HAS_ONE_JOB,
        topic="office dog",
        deterministic_seed=0,
    )
    valid = MockTextProvider().generate_draft(request)
    scenes = [scene.model_dump() for scene in valid.scenes]
    scenes[1]["visual_type"] = "VIDEO"

    with pytest.raises(ValidationError, match="visual budget"):
        StructuredDraft.model_validate({**valid.model_dump(), "scenes": scenes})


def test_dog_draft_requires_synthetic_media_disclosure() -> None:
    request = DraftRequest(
        video_id=UUID(int=15),
        arm=ContentArm.DOGS,
        format=ContentFormat.DOG_HAS_ONE_JOB,
        topic="office dog",
        deterministic_seed=0,
    )
    valid = MockTextProvider().generate_draft(request)

    with pytest.raises(ValidationError, match="must disclose synthetic media"):
        StructuredDraft.model_validate({**valid.model_dump(), "contains_synthetic_media": False})
