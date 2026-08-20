from pathlib import Path

import pytest

from shorts_automation.observability.secret_scan import scan_paths


@pytest.mark.parametrize(
    "credential_name",
    [
        "OPENAI_API_KEY",
        "RUNWAYML_API_SECRET",
        "USDA_API_KEY",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_REFRESH_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
    ],
)
def test_nonblank_project_credential_assignment_is_detected(
    tmp_path: Path, credential_name: str
) -> None:
    candidate = tmp_path / "candidate.env"
    candidate.write_text(f"{credential_name}=fixture-nonblank-value\n", encoding="utf-8")

    assert "nonblank project credential assignment" in scan_paths([candidate])[0]


def test_blank_example_placeholders_are_allowed(tmp_path: Path) -> None:
    candidate = tmp_path / ".env.example"
    candidate.write_text("OPENAI_API_KEY=\nYOUTUBE_REFRESH_TOKEN=\n", encoding="utf-8")

    assert scan_paths([candidate]) == []
