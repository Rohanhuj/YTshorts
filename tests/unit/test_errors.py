from shorts_automation.domain.errors import ErrorCode, ShortsAutomationError


def test_typed_error_preserves_machine_readable_code() -> None:
    error = ShortsAutomationError(ErrorCode.BUDGET_EXCEEDED, "fixture budget stop")

    assert str(error) == "fixture budget stop"
    assert error.code is ErrorCode.BUDGET_EXCEEDED
