"""Typed domain errors with machine-readable error codes."""

from enum import StrEnum


class ErrorCode(StrEnum):
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    FACT_CHECK_FAILED = "FACT_CHECK_FAILED"
    SAFETY_REJECTED = "SAFETY_REJECTED"
    PROVIDER_TRANSIENT_ERROR = "PROVIDER_TRANSIENT_ERROR"
    PROVIDER_PERMANENT_ERROR = "PROVIDER_PERMANENT_ERROR"
    RENDER_FAILED = "RENDER_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    OAUTH_REVOKED = "OAUTH_REVOKED"
    UPLOAD_REJECTED = "UPLOAD_REJECTED"
    YOUTUBE_PROCESSING_FAILED = "YOUTUBE_PROCESSING_FAILED"
    DUPLICATE_PREVENTED = "DUPLICATE_PREVENTED"
    STATE_CONFLICT = "STATE_CONFLICT"


class ShortsAutomationError(Exception):
    """Base exception that preserves a stable error category."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class StateTransitionError(ShortsAutomationError):
    """Raised when a workflow requests an invalid state transition."""

    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.STATE_CONFLICT, message)
