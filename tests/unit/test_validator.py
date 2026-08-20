import json
from pathlib import Path

import pytest

from shorts_automation.domain.errors import ErrorCode, ShortsAutomationError
from shorts_automation.production.validator import FfprobeValidator


def _payload(**video_changes: object) -> str:
    video = {
        "codec_type": "video",
        "codec_name": "h264",
        "width": 720,
        "height": 1280,
        "pix_fmt": "yuv420p",
        "avg_frame_rate": "30/1",
        "nb_read_frames": "720",
    }
    video.update(video_changes)
    return json.dumps(
        {
            "streams": [video],
            "format": {
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "24.000",
                "size": "1000",
            },
        }
    )


def _lit_frame(_command: object) -> str:
    return "lavfi.signalstats.YAVG=80"


def test_valid_probe_payload_is_normalized() -> None:
    result = FfprobeValidator(runner=lambda _command: _payload(), frame_runner=_lit_frame).validate(
        Path("fixture.mp4")
    )
    assert (result.width, result.height, result.frames_per_second, result.frame_count) == (
        720,
        1280,
        30,
        720,
    )
    assert result.has_audio is False


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"codec_name": "vp9"}, "H.264"),
        ({"width": 1280, "height": 720}, "dimensions"),
        ({"avg_frame_rate": "25/1", "nb_read_frames": "600"}, "30 fps"),
        ({"pix_fmt": "yuv444p"}, "yuv420p"),
        ({"nb_read_frames": "1"}, "frame count"),
    ],
)
def test_invalid_media_fails_closed(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ShortsAutomationError, match=message) as exc_info:
        FfprobeValidator(
            runner=lambda _command: _payload(**changes), frame_runner=_lit_frame
        ).validate(Path("fixture.mp4"))
    assert exc_info.value.code is ErrorCode.VALIDATION_FAILED


def test_malformed_probe_response_fails_closed() -> None:
    with pytest.raises(ShortsAutomationError) as exc_info:
        FfprobeValidator(runner=lambda _command: "not-json", frame_runner=_lit_frame).validate(
            Path("fixture.mp4")
        )
    assert exc_info.value.code is ErrorCode.VALIDATION_FAILED


@pytest.mark.parametrize(
    "payload",
    [
        {"streams": [None], "format": {}},
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 720,
                    "height": 1280,
                    "pix_fmt": "yuv420p",
                    "avg_frame_rate": "1/0",
                    "nb_read_frames": "1",
                }
            ],
            "format": {"format_name": "mp4", "duration": "24", "size": "1"},
        },
    ],
)
def test_malformed_probe_shapes_are_normalized(payload: object) -> None:
    with pytest.raises(ShortsAutomationError) as exc_info:
        FfprobeValidator(
            runner=lambda _command: json.dumps(payload), frame_runner=_lit_frame
        ).validate(Path("fixture.mp4"))
    assert exc_info.value.code is ErrorCode.VALIDATION_FAILED


def test_black_first_frame_is_rejected() -> None:
    validator = FfprobeValidator(
        runner=lambda _command: _payload(),
        frame_runner=lambda _command: "lavfi.signalstats.YAVG=16",
    )
    with pytest.raises(ShortsAutomationError, match="black or empty"):
        validator.validate(Path("fixture.mp4"))


def test_missing_first_frame_measurement_is_rejected() -> None:
    validator = FfprobeValidator(
        runner=lambda _command: _payload(), frame_runner=lambda _command: ""
    )
    with pytest.raises(ShortsAutomationError, match="luminance"):
        validator.validate(Path("fixture.mp4"))


def test_expected_audio_requires_aac_stream() -> None:
    payload = json.loads(_payload())
    payload["streams"].append({"codec_type": "audio", "codec_name": "mp3"})
    with pytest.raises(ShortsAutomationError, match="AAC"):
        FfprobeValidator(
            runner=lambda _command: json.dumps(payload), frame_runner=_lit_frame
        ).validate(Path("fixture.mp4"), audio_expected=True)
