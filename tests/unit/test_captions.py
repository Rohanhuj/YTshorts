from uuid import UUID

from shorts_automation.domain.models import ContentArm, ContentFormat, StructuredDraft
from shorts_automation.production.captions import CaptionStyle, build_ass
from shorts_automation.providers.interfaces import DraftRequest
from shorts_automation.providers.mocks import MockTextProvider


def _draft() -> StructuredDraft:
    return MockTextProvider().generate_draft(
        DraftRequest(
            video_id=UUID(int=1),
            arm=ContentArm.FOOD,
            format=ContentFormat.PICK_ONE,
            topic="fixture food",
            deterministic_seed=0,
        )
    )


def test_ass_captions_are_cumulative_and_inside_safe_margins() -> None:
    result = build_ass(_draft(), CaptionStyle(1080, 1920, 120, "DejaVu Sans"))

    assert "PlayResX: 1080\nPlayResY: 1920" in result
    assert ",120,120,120,1" in result
    assert "Dialogue: 0,0:00:00.00,0:00:06.00" in result
    assert "Dialogue: 0,0:00:18.00,0:00:24.00" in result
    assert result.count("Dialogue:") == 4


def test_ass_caption_text_escapes_markup_and_wraps() -> None:
    draft = _draft()
    scenes = [
        scene.model_copy(
            update={"caption": r"A {very} long caption with enough words to wrap safely on mobile"}
        )
        if scene.scene_number == 1
        else scene
        for scene in draft.scenes
    ]
    changed = draft.model_copy(update={"scenes": tuple(scenes)})

    result = build_ass(changed, CaptionStyle(720, 1280, 96, "DejaVu Sans"))

    assert r"\{very\}" in result
    assert r"\N" in result
