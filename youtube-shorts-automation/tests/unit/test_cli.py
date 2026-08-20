import json
import sys
from pathlib import Path

import pytest

from shorts_automation import cli

CONFIG_DIR = Path(__file__).parents[2] / "config"


def test_validate_mocks_cli_reports_all_three_arms(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["shorts-automation", "validate-mocks"])

    assert cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert [draft["arm"] for draft in result["mock_drafts"]] == ["FOOD", "COOKING", "DOGS"]
    assert all(draft["valid"] for draft in result["mock_drafts"])


def test_validate_config_cli_reports_safe_defaults(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["shorts-automation", "validate-config", "--config-dir", str(CONFIG_DIR)],
    )
    monkeypatch.delenv("PUBLISHING_ENABLED", raising=False)

    assert cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["publishing_enabled"] is False
    assert result["monthly_budget_usd"] == 45.0


def test_cli_requires_a_known_subcommand(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["shorts-automation"])

    with pytest.raises(SystemExit):
        cli.main()
