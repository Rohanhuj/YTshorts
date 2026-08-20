"""Strict YAML configuration loader with a small set of safe environment overrides."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from shorts_automation.domain.models import ContentArm, ContentFormat


class ArmDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target_count: int = Field(gt=0)
    formats: tuple[ContentFormat, ...] = Field(min_length=1)


class ArmsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    initial_experiment_videos: int = Field(gt=0)
    adaptive_allocation_enabled: bool
    arms: dict[ContentArm, ArmDefinition]

    @model_validator(mode="after")
    def allocation_matches_experiment(self) -> Self:
        if set(self.arms) != set(ContentArm):
            raise ValueError("all three content arms must be configured")
        if sum(arm.target_count for arm in self.arms.values()) != self.initial_experiment_videos:
            raise ValueError("arm target counts must equal initial_experiment_videos")
        for arm, definition in self.arms.items():
            if any(
                content_format not in _formats_for_arm(arm) for content_format in definition.formats
            ):
                raise ValueError(f"configured format does not belong to {arm}")
        return self


class ScheduleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    timezone: str
    daily_slots: tuple[str, str]
    minimum_schedule_lead_hours: int = Field(ge=1)
    arm_cycle: tuple[tuple[ContentArm, ContentArm], ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_schedule(self) -> Self:
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {self.timezone}") from exc
        for slot in self.daily_slots:
            parts = slot.split(":")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                raise ValueError("daily slots must use HH:MM:SS")
            hour, minute, second = (int(part) for part in parts)
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError(f"invalid daily slot: {slot}")
        return self


class BudgetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    monthly_hard_limit_usd: float = Field(gt=0, le=45.0)
    daily_generation_limit_usd: float = Field(gt=0)
    per_video_target_usd: float = Field(gt=0)
    per_video_hard_limit_usd: float = Field(gt=0)
    max_image_attempts_per_scene: int = Field(ge=1)
    max_video_attempts_per_video: int = Field(ge=1)
    default_ai_video_seconds: int = Field(ge=1)

    @model_validator(mode="after")
    def limits_must_be_nested(self) -> Self:
        if self.per_video_target_usd > self.per_video_hard_limit_usd:
            raise ValueError("per-video target cannot exceed per-video hard limit")
        if self.per_video_hard_limit_usd > self.daily_generation_limit_usd:
            raise ValueError("per-video hard limit cannot exceed daily generation limit")
        if self.daily_generation_limit_usd > self.monthly_hard_limit_usd:
            raise ValueError("daily generation limit cannot exceed monthly hard limit")
        return self


class StylesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    canvas_width: int = Field(gt=0)
    canvas_height: int = Field(gt=0)
    frames_per_second: int = Field(gt=0)
    minimum_duration_seconds: int = Field(gt=0)
    maximum_duration_seconds: int = Field(gt=0)
    hard_maximum_duration_seconds: int = Field(gt=0, lt=60)
    caption_safe_margin_pixels: int = Field(ge=0)
    default_font: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_media_limits(self) -> Self:
        if self.canvas_width * 16 != self.canvas_height * 9:
            raise ValueError("canvas must have an exact 9:16 aspect ratio")
        if not (
            self.minimum_duration_seconds
            <= self.maximum_duration_seconds
            <= self.hard_maximum_duration_seconds
        ):
            raise ValueError("duration limits must be ordered")
        return self


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    arms: ArmsConfig
    schedule: ScheduleConfig
    budget: BudgetConfig
    styles: StylesConfig
    mock_mode: bool = True
    publishing_enabled: bool = False


def _formats_for_arm(arm: ContentArm) -> frozenset[ContentFormat]:
    from shorts_automation.domain.models import FORMATS_BY_ARM

    return FORMATS_BY_ARM[arm]


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing configuration file: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"configuration root must be a mapping: {path}")
    return raw


def _read_bool(environment: Mapping[str, str], key: str, default: bool) -> bool:
    raw = environment.get(key)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{key} must be true or false")
    return normalized == "true"


def load_config(config_dir: Path, environment: Mapping[str, str] | None = None) -> AppConfig:
    """Load the four checked-in YAML files and approved environment overrides."""
    env = environment or {}
    schedule_data = _read_yaml(config_dir / "schedule.yaml")
    budget_data = _read_yaml(config_dir / "budget.yaml")
    if timezone_name := env.get("PUBLISH_TIMEZONE"):
        schedule_data["timezone"] = timezone_name
    if monthly_budget := env.get("MONTHLY_BUDGET_USD"):
        budget_data["monthly_hard_limit_usd"] = float(monthly_budget)

    return AppConfig(
        arms=ArmsConfig.model_validate(_read_yaml(config_dir / "arms.yaml")),
        schedule=ScheduleConfig.model_validate(schedule_data),
        budget=BudgetConfig.model_validate(budget_data),
        styles=StylesConfig.model_validate(_read_yaml(config_dir / "styles.yaml")),
        mock_mode=_read_bool(env, "MOCK_MODE", True),
        publishing_enabled=_read_bool(env, "PUBLISHING_ENABLED", False),
    )
