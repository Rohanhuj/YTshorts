"""Deterministic, zero-cost providers used by CI and local development."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from pydantic import HttpUrl

from shorts_automation.domain.models import (
    ContentArm,
    FactCitation,
    FactSourceType,
    Scene,
    StructuredDraft,
    VisualType,
)
from shorts_automation.providers.interfaces import (
    DraftRequest,
    FactRecord,
    GeneratedAsset,
    ImageRequest,
    UploadRequest,
    UploadResult,
    VideoRequest,
)


class _ArmCopy(TypedDict):
    hook: str
    captions: tuple[str, str, str, str]
    title: str
    description: str
    comment: str


_ARM_COPY_BY_ARM: dict[ContentArm, _ArmCopy] = {
    ContentArm.FOOD: {
        "hook": "Which breakfast has more protein?",
        "captions": (
            "Pick one",
            "Eggs or oatmeal?",
            "Three, two, one",
            "Eggs win this round",
        ),
        "title": "Eggs vs Oatmeal: Protein Pick",
        "description": "A sourced breakfast comparison using USDA FoodData Central.",
        "comment": "Which would you pick?",
    },
    ContentArm.COOKING: {
        "hook": "Can three ingredients become crispy potato bites?",
        "captions": (
            "The finished bite",
            "Only three ingredients",
            "Shape and bake",
            "The crispy reveal",
        ),
        "title": "Three-Ingredient Potato Bite Challenge",
        "description": (
            "A synthetic cooking concept; this generated recipe was not physically tested."
        ),
        "comment": "Would you try this?",
    },
    ContentArm.DOGS: {
        "hook": "The office dog got one very important job.",
        "captions": (
            "First day at work",
            "One important delivery",
            "A tiny detour",
            "Employee of the month",
        ),
        "title": "The Office Dog Had One Job",
        "description": "A fictional, AI-generated dog mini-story made for entertainment.",
        "comment": "Did the dog earn a promotion?",
    },
}


class MockTextProvider:
    """Return a repeatable schema-valid draft for each supported content arm."""

    def generate_draft(self, request: DraftRequest) -> StructuredDraft:
        arm_copy = _ARM_COPY_BY_ARM[request.arm]
        visual_types = (
            VisualType.VIDEO,
            VisualType.IMAGE,
            VisualType.IMAGE,
            VisualType.IMAGE,
        )
        scenes = tuple(
            Scene(
                scene_number=index,
                duration_seconds=6,
                narration=None,
                caption=caption,
                visual_prompt=(
                    f"Vertical 9:16 synthetic {request.arm.value.lower()} scene {index}; "
                    f"family-safe, original composition, no brands, no logos"
                ),
                visual_type=visual_types[index - 1],
            )
            for index, caption in enumerate(arm_copy["captions"], start=1)
        )
        facts: tuple[FactCitation, ...] = ()
        if request.arm in {ContentArm.FOOD, ContentArm.COOKING}:
            facts = (
                FactCitation(
                    claim="The factual food reference is grounded in a sanitized USDA fixture.",
                    source_type=FactSourceType.USDA_FDC,
                    source_id="fixture-fdc-001",
                    source_url=HttpUrl("https://fdc.nal.usda.gov/"),
                ),
            )
        return StructuredDraft(
            video_id=request.video_id,
            arm=request.arm,
            format=request.format,
            topic=request.topic,
            hook=arm_copy["hook"],
            target_duration_seconds=24,
            scenes=scenes,
            facts=facts,
            title=arm_copy["title"],
            description=arm_copy["description"],
            tags=(request.arm.value.lower(), "shorts", "synthetic-media"),
            comment_prompt=arm_copy["comment"],
            contains_synthetic_media=True,
            made_for_kids=False,
        )


class MockVisualProvider:
    """Return deterministic asset metadata without writing files or calling a provider."""

    @staticmethod
    def _asset(media_type: str, idempotency_key: str) -> GeneratedAsset:
        digest = hashlib.sha256(f"mock:{media_type}:{idempotency_key}".encode()).hexdigest()
        return GeneratedAsset(
            asset_id=f"mock-{digest[:16]}",
            media_type=media_type,
            local_path=Path(f"fixtures/{digest[:16]}.{media_type}"),
            sha256=digest,
            provider_request_id=f"mock-request-{digest[:12]}",
            actual_cost_usd=0.0,
        )

    def generate_image(self, request: ImageRequest) -> GeneratedAsset:
        return self._asset("png", request.idempotency_key)

    def generate_video(self, request: VideoRequest) -> GeneratedAsset:
        return self._asset("mp4", request.idempotency_key)


class MockFactProvider:
    def search(self, query: str) -> list[FactRecord]:
        return [
            FactRecord(
                source_id="fixture-fdc-001",
                source_url="https://fdc.nal.usda.gov/",
                claim=f"Sanitized deterministic fact fixture for: {query}",
            )
        ]


class MockPublishingProvider:
    """Model private upload behavior without accessing credentials or a network."""

    def __init__(self) -> None:
        self.scheduled: dict[str, datetime] = {}

    def upload_private(self, request: UploadRequest) -> UploadResult:
        digest = hashlib.sha256(request.idempotency_key.encode()).hexdigest()
        return UploadResult(youtube_video_id=f"mock-{digest[:11]}", privacy_status="private")

    def schedule(self, video_id: str, publish_at: datetime) -> None:
        if publish_at.tzinfo is None or publish_at <= datetime.now(UTC):
            raise ValueError("publish_at must be timezone-aware and in the future")
        self.scheduled[video_id] = publish_at
