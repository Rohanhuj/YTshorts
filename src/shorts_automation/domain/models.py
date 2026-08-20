"""Validated domain records independent of vendors and orchestration."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ContentArm(StrEnum):
    FOOD = "FOOD"
    COOKING = "COOKING"
    DOGS = "DOGS"


class ContentFormat(StrEnum):
    PICK_ONE = "PICK_ONE"
    GUESS_THE_FOOD = "GUESS_THE_FOOD"
    PRICE_COMPARISON = "PRICE_COMPARISON"
    PORTION_COMPARISON = "PORTION_COMPARISON"
    NUTRIENT_REVEAL = "NUTRIENT_REVEAL"
    THREE_INGREDIENT_CHALLENGE = "THREE_INGREDIENT_CHALLENGE"
    FOOD_TRANSFORMATION = "FOOD_TRANSFORMATION"
    ONE_INGREDIENT_THREE_WAYS = "ONE_INGREDIENT_THREE_WAYS"
    BUDGET_MEAL = "BUDGET_MEAL"
    COOKING_EXPERIMENT = "COOKING_EXPERIMENT"
    FUNNY_POV = "FUNNY_POV"
    DOG_HAS_ONE_JOB = "DOG_HAS_ONE_JOB"
    DOG_CHOOSES = "DOG_CHOOSES"
    WHOLESOME_MINI_STORY = "WHOLESOME_MINI_STORY"
    FICTIONAL_ADVENTURE = "FICTIONAL_ADVENTURE"


FORMATS_BY_ARM: dict[ContentArm, frozenset[ContentFormat]] = {
    ContentArm.FOOD: frozenset(
        {
            ContentFormat.PICK_ONE,
            ContentFormat.GUESS_THE_FOOD,
            ContentFormat.PRICE_COMPARISON,
            ContentFormat.PORTION_COMPARISON,
            ContentFormat.NUTRIENT_REVEAL,
        }
    ),
    ContentArm.COOKING: frozenset(
        {
            ContentFormat.THREE_INGREDIENT_CHALLENGE,
            ContentFormat.FOOD_TRANSFORMATION,
            ContentFormat.ONE_INGREDIENT_THREE_WAYS,
            ContentFormat.BUDGET_MEAL,
            ContentFormat.COOKING_EXPERIMENT,
        }
    ),
    ContentArm.DOGS: frozenset(
        {
            ContentFormat.FUNNY_POV,
            ContentFormat.DOG_HAS_ONE_JOB,
            ContentFormat.DOG_CHOOSES,
            ContentFormat.WHOLESOME_MINI_STORY,
            ContentFormat.FICTIONAL_ADVENTURE,
        }
    ),
}


class VisualType(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class FactSourceType(StrEnum):
    USDA_FDC = "USDA_FDC"
    APPROVED_SOURCE = "APPROVED_SOURCE"


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scene_number: int = Field(ge=1)
    duration_seconds: float = Field(gt=0, le=15)
    narration: str | None = Field(default=None, max_length=300)
    caption: str = Field(min_length=1, max_length=100)
    visual_prompt: str = Field(min_length=10, max_length=1_000)
    visual_type: VisualType


class FactCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim: str = Field(min_length=3, max_length=500)
    source_type: FactSourceType
    source_id: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl


class StructuredDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    video_id: UUID
    arm: ContentArm
    format: ContentFormat
    topic: str = Field(min_length=3, max_length=150)
    hook: str = Field(min_length=3, max_length=120)
    target_duration_seconds: float = Field(ge=15, le=35)
    scenes: tuple[Scene, ...] = Field(min_length=3, max_length=8)
    facts: tuple[FactCitation, ...] = ()
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5_000)
    tags: tuple[str, ...] = Field(min_length=1, max_length=15)
    comment_prompt: str = Field(min_length=2, max_length=120)
    contains_synthetic_media: bool
    made_for_kids: bool

    @model_validator(mode="after")
    def validate_draft_contract(self) -> Self:
        if self.format not in FORMATS_BY_ARM[self.arm]:
            raise ValueError(f"format {self.format} is not allowed for arm {self.arm}")

        expected_numbers = tuple(range(1, len(self.scenes) + 1))
        actual_numbers = tuple(scene.scene_number for scene in self.scenes)
        if actual_numbers != expected_numbers:
            raise ValueError("scene numbers must be sequential and start at 1")

        scene_duration = sum(scene.duration_seconds for scene in self.scenes)
        if abs(scene_duration - self.target_duration_seconds) > 0.05:
            raise ValueError("scene durations must sum to target_duration_seconds")

        image_count = sum(scene.visual_type is VisualType.IMAGE for scene in self.scenes)
        video_count = sum(scene.visual_type is VisualType.VIDEO for scene in self.scenes)
        if image_count > 6 or video_count > 1:
            raise ValueError("visual budget allows at most six images and one video")

        if self.arm in {ContentArm.FOOD, ContentArm.COOKING} and not self.facts:
            raise ValueError("food and cooking drafts require approved factual citations")
        if self.arm is ContentArm.DOGS and not self.contains_synthetic_media:
            raise ValueError("fictional dog drafts must disclose synthetic media")

        return self


class VideoState(StrEnum):
    PLANNED = "PLANNED"
    SCRIPTED = "SCRIPTED"
    FACT_CHECKED = "FACT_CHECKED"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    RENDERING = "RENDERING"
    VALIDATING = "VALIDATING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    UPLOADING = "UPLOADING"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    MEASURING = "MEASURING"
    COMPLETE = "COMPLETE"
    GENERATION_FAILED = "GENERATION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    old_state: VideoState
    new_state: VideoState
    timestamp: datetime
    workflow_run_id: str = Field(min_length=1, max_length=200)
    actor: str = Field(min_length=1, max_length=200)
    attempt_number: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=1_000)
    error_code: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def timestamp_must_be_utc(self) -> Self:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() != UTC.utcoffset(None):
            raise ValueError("audit timestamp must be timezone-aware UTC")
        return self


class VideoRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    video_id: UUID = Field(default_factory=uuid4)
    state: VideoState = VideoState.PLANNED
    version: int = Field(default=0, ge=0)
    audit_events: tuple[AuditEvent, ...] = ()
