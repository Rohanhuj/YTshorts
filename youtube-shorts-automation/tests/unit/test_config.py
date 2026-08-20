from pathlib import Path

import pytest
from pydantic import ValidationError

from shorts_automation.config import load_config

CONFIG_DIR = Path(__file__).parents[2] / "config"


def test_checked_in_configuration_is_valid_and_safe_by_default() -> None:
    config = load_config(CONFIG_DIR)

    assert config.mock_mode is True
    assert config.publishing_enabled is False
    assert config.schedule.timezone == "America/Los_Angeles"
    assert config.budget.monthly_hard_limit_usd == 45.0
    assert sum(arm.target_count for arm in config.arms.arms.values()) == 30


def test_approved_environment_overrides_are_applied() -> None:
    config = load_config(
        CONFIG_DIR,
        {
            "PUBLISH_TIMEZONE": "America/New_York",
            "MONTHLY_BUDGET_USD": "40.00",
            "MOCK_MODE": "false",
            "PUBLISHING_ENABLED": "false",
        },
    )

    assert config.schedule.timezone == "America/New_York"
    assert config.budget.monthly_hard_limit_usd == 40.0
    assert config.mock_mode is False


def test_invalid_boolean_environment_value_fails_closed() -> None:
    with pytest.raises(ValueError, match="must be true or false"):
        load_config(CONFIG_DIR, {"PUBLISHING_ENABLED": "yes"})


def test_monthly_override_cannot_break_nested_budget_limits() -> None:
    with pytest.raises(ValidationError, match="daily generation limit"):
        load_config(CONFIG_DIR, {"MONTHLY_BUDGET_USD": "1.00"})


def test_monthly_override_cannot_raise_locked_hard_cap() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 45"):
        load_config(CONFIG_DIR, {"MONTHLY_BUDGET_USD": "45.01"})


def test_non_finite_monthly_override_fails_closed() -> None:
    with pytest.raises(ValidationError):
        load_config(CONFIG_DIR, {"MONTHLY_BUDGET_USD": "inf"})


def test_missing_configuration_file_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing configuration file"):
        load_config(tmp_path)


def test_configuration_root_must_be_mapping(tmp_path: Path) -> None:
    for name in ("schedule.yaml", "budget.yaml", "styles.yaml"):
        (tmp_path / name).write_text("{}", encoding="utf-8")
    (tmp_path / "arms.yaml").write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="root must be a mapping"):
        load_config(tmp_path)


def test_invalid_timezone_fails_closed() -> None:
    with pytest.raises(ValidationError, match="unknown timezone"):
        load_config(CONFIG_DIR, {"PUBLISH_TIMEZONE": "Not/A_Real_Zone"})


def test_true_boolean_override_is_parsed() -> None:
    config = load_config(CONFIG_DIR, {"PUBLISHING_ENABLED": "true"})

    assert config.publishing_enabled is True
