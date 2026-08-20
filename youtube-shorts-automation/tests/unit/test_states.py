from datetime import UTC, datetime

import pytest

from shorts_automation.domain.errors import ErrorCode, StateTransitionError
from shorts_automation.domain.models import VideoRecord, VideoState
from shorts_automation.domain.states import transition_record, validate_transition

FROZEN_NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def test_valid_transition_appends_immutable_audit_event() -> None:
    original = VideoRecord()

    updated = transition_record(
        original,
        VideoState.SCRIPTED,
        workflow_run_id="run-123",
        actor="mock-test",
        attempt_number=1,
        now=FROZEN_NOW,
    )

    assert original.state is VideoState.PLANNED
    assert updated.state is VideoState.SCRIPTED
    assert updated.version == 1
    assert len(updated.audit_events) == 1
    assert updated.audit_events[0].timestamp == FROZEN_NOW
    assert updated.audit_events[0].video_id == original.video_id


@pytest.mark.parametrize(
    ("old_state", "new_state"),
    [
        (VideoState.PLANNED, VideoState.APPROVED),
        (VideoState.NEEDS_REVIEW, VideoState.SCHEDULED),
        (VideoState.REJECTED, VideoState.APPROVED),
        (VideoState.COMPLETE, VideoState.MEASURING),
    ],
)
def test_invalid_or_bypass_transition_is_rejected(
    old_state: VideoState, new_state: VideoState
) -> None:
    with pytest.raises(StateTransitionError) as exc_info:
        validate_transition(old_state, new_state)
    assert exc_info.value.code is ErrorCode.STATE_CONFLICT


def test_duplicate_transition_is_rejected() -> None:
    with pytest.raises(StateTransitionError, match="not allowed"):
        validate_transition(VideoState.NEEDS_REVIEW, VideoState.NEEDS_REVIEW)


@pytest.mark.parametrize(
    "failure_state",
    [VideoState.UPLOAD_FAILED, VideoState.PROCESSING_FAILED],
)
def test_ambiguous_upload_failure_cannot_blindly_retry(failure_state: VideoState) -> None:
    with pytest.raises(StateTransitionError, match="not allowed"):
        validate_transition(failure_state, VideoState.UPLOADING)


@pytest.mark.parametrize("failed_state", [VideoState.VALIDATION_FAILED, VideoState.REJECTED])
def test_failed_content_must_return_through_script_and_fact_check(
    failed_state: VideoState,
) -> None:
    with pytest.raises(StateTransitionError, match="not allowed"):
        validate_transition(failed_state, VideoState.GENERATING)
    validate_transition(failed_state, VideoState.SCRIPTED)
    validate_transition(VideoState.SCRIPTED, VideoState.FACT_CHECKED)
    validate_transition(VideoState.FACT_CHECKED, VideoState.GENERATING)


def test_arbitrary_string_state_is_rejected() -> None:
    with pytest.raises(StateTransitionError, match="enum members"):
        validate_transition(VideoState.PLANNED, "SCRIPTED")  # type: ignore[arg-type]


def test_non_utc_audit_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="UTC"):
        transition_record(
            VideoRecord(),
            VideoState.SCRIPTED,
            workflow_run_id="run-123",
            actor="mock-test",
            attempt_number=1,
            now=datetime(2026, 8, 20, 12, 0),
        )
