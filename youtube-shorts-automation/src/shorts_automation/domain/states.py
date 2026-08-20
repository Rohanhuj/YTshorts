"""Central state machine for idempotent workflow transitions."""

from datetime import UTC, datetime

from shorts_automation.domain.errors import StateTransitionError
from shorts_automation.domain.models import AuditEvent, VideoRecord, VideoState

ALLOWED_TRANSITIONS: dict[VideoState, frozenset[VideoState]] = {
    VideoState.PLANNED: frozenset({VideoState.SCRIPTED, VideoState.CANCELLED}),
    VideoState.SCRIPTED: frozenset(
        {VideoState.FACT_CHECKED, VideoState.VALIDATION_FAILED, VideoState.CANCELLED}
    ),
    VideoState.FACT_CHECKED: frozenset(
        {VideoState.GENERATING, VideoState.VALIDATION_FAILED, VideoState.CANCELLED}
    ),
    VideoState.GENERATING: frozenset(
        {VideoState.GENERATED, VideoState.GENERATION_FAILED, VideoState.CANCELLED}
    ),
    VideoState.GENERATION_FAILED: frozenset({VideoState.GENERATING, VideoState.CANCELLED}),
    VideoState.GENERATED: frozenset({VideoState.RENDERING, VideoState.CANCELLED}),
    VideoState.RENDERING: frozenset(
        {VideoState.VALIDATING, VideoState.VALIDATION_FAILED, VideoState.CANCELLED}
    ),
    VideoState.VALIDATING: frozenset(
        {VideoState.NEEDS_REVIEW, VideoState.VALIDATION_FAILED, VideoState.CANCELLED}
    ),
    VideoState.VALIDATION_FAILED: frozenset(
        {VideoState.SCRIPTED, VideoState.REJECTED, VideoState.CANCELLED}
    ),
    VideoState.NEEDS_REVIEW: frozenset(
        {VideoState.APPROVED, VideoState.REJECTED, VideoState.CANCELLED}
    ),
    VideoState.REJECTED: frozenset({VideoState.SCRIPTED, VideoState.CANCELLED}),
    VideoState.APPROVED: frozenset({VideoState.UPLOADING, VideoState.CANCELLED}),
    VideoState.UPLOADING: frozenset(
        {VideoState.SCHEDULED, VideoState.UPLOAD_FAILED, VideoState.PROCESSING_FAILED}
    ),
    # Upload failures remain fail-closed until a later reconciliation service can prove whether
    # YouTube created an upload. Generic transitions must never encode a blind re-upload.
    VideoState.UPLOAD_FAILED: frozenset({VideoState.CANCELLED}),
    VideoState.PROCESSING_FAILED: frozenset({VideoState.CANCELLED}),
    VideoState.SCHEDULED: frozenset({VideoState.PUBLISHED, VideoState.CANCELLED}),
    VideoState.PUBLISHED: frozenset({VideoState.MEASURING}),
    VideoState.MEASURING: frozenset({VideoState.COMPLETE}),
    VideoState.COMPLETE: frozenset(),
    VideoState.CANCELLED: frozenset(),
}


def validate_transition(old_state: VideoState, new_state: VideoState) -> None:
    """Reject arbitrary values, repeats, and transitions outside the central graph."""
    if not isinstance(old_state, VideoState) or not isinstance(new_state, VideoState):
        raise StateTransitionError("states must be VideoState enum members")
    if new_state not in ALLOWED_TRANSITIONS[old_state]:
        raise StateTransitionError(f"transition {old_state} -> {new_state} is not allowed")


def transition_record(
    record: VideoRecord,
    new_state: VideoState,
    *,
    workflow_run_id: str,
    actor: str,
    attempt_number: int,
    now: datetime | None = None,
    reason: str | None = None,
    error_code: str | None = None,
) -> VideoRecord:
    """Return a new immutable record with one immutable UTC audit event."""
    validate_transition(record.state, new_state)
    timestamp = now or datetime.now(UTC)
    event = AuditEvent(
        video_id=record.video_id,
        old_state=record.state,
        new_state=new_state,
        timestamp=timestamp,
        workflow_run_id=workflow_run_id,
        actor=actor,
        attempt_number=attempt_number,
        reason=reason,
        error_code=error_code,
    )
    return record.model_copy(
        update={
            "state": new_state,
            "version": record.version + 1,
            "audit_events": (*record.audit_events, event),
        }
    )
