"""Small Phase 0 CLI for configuration and deterministic contract verification."""

import argparse
import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from shorts_automation.config import load_config
from shorts_automation.domain.models import ContentArm, ContentFormat
from shorts_automation.providers.interfaces import DraftRequest
from shorts_automation.providers.mocks import MockTextProvider

DEFAULT_FORMATS = {
    ContentArm.FOOD: ContentFormat.PICK_ONE,
    ContentArm.COOKING: ContentFormat.THREE_INGREDIENT_CHALLENGE,
    ContentArm.DOGS: ContentFormat.DOG_HAS_ONE_JOB,
}


def _validate_mocks() -> int:
    provider = MockTextProvider()
    results: list[dict[str, object]] = []
    for arm in ContentArm:
        request = DraftRequest(
            video_id=uuid5(NAMESPACE_URL, f"shorts-automation:{arm.value}"),
            arm=arm,
            format=DEFAULT_FORMATS[arm],
            topic=f"Phase 0 deterministic {arm.value.lower()} fixture",
            deterministic_seed=0,
        )
        draft = provider.generate_draft(request)
        results.append(
            {
                "arm": draft.arm.value,
                "format": draft.format.value,
                "scene_count": len(draft.scenes),
                "duration_seconds": draft.target_duration_seconds,
                "valid": True,
            }
        )
    print(json.dumps({"mock_drafts": results}, indent=2, sort_keys=True))
    return 0


def _validate_config(config_dir: Path) -> int:
    config = load_config(config_dir, os.environ)
    print(
        json.dumps(
            {
                "mock_mode": config.mock_mode,
                "publishing_enabled": config.publishing_enabled,
                "timezone": config.schedule.timezone,
                "monthly_budget_usd": config.budget.monthly_hard_limit_usd,
                "arms": sorted(arm.value for arm in config.arms.arms),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shorts-automation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-mocks", help="validate one deterministic draft per arm")
    config_parser = subparsers.add_parser("validate-config", help="load and validate YAML config")
    config_parser.add_argument("--config-dir", type=Path, default=Path("config"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-mocks":
        return _validate_mocks()
    if args.command == "validate-config":
        return _validate_config(args.config_dir)
    raise AssertionError(f"unhandled command: {args.command}")
