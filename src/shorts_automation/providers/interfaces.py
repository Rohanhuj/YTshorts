"""Typed ports that isolate domain logic from vendor SDKs."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from shorts_automation.domain.models import ContentArm, ContentFormat, StructuredDraft


@dataclass(frozen=True, slots=True)
class DraftRequest:
    video_id: UUID
    arm: ContentArm
    format: ContentFormat
    topic: str
    deterministic_seed: int


@dataclass(frozen=True, slots=True)
class ImageRequest:
    video_id: UUID
    scene_number: int
    prompt: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class VideoRequest:
    video_id: UUID
    scene_number: int
    prompt: str
    duration_seconds: int
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class GeneratedAsset:
    asset_id: str
    media_type: str
    local_path: Path
    sha256: str
    provider_request_id: str
    actual_cost_usd: float


@dataclass(frozen=True, slots=True)
class FactRecord:
    source_id: str
    source_url: str
    claim: str


@dataclass(frozen=True, slots=True)
class UploadRequest:
    video_id: UUID
    file_path: Path
    artifact_sha256: str
    title: str
    description: str
    made_for_kids: bool
    contains_synthetic_media: bool
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class UploadResult:
    youtube_video_id: str
    privacy_status: str


class TextProvider(Protocol):
    def generate_draft(self, request: DraftRequest) -> StructuredDraft: ...


class VisualProvider(Protocol):
    def generate_image(self, request: ImageRequest) -> GeneratedAsset: ...

    def generate_video(self, request: VideoRequest) -> GeneratedAsset: ...


class FactProvider(Protocol):
    def search(self, query: str) -> list[FactRecord]: ...


class PublishingProvider(Protocol):
    def upload_private(self, request: UploadRequest) -> UploadResult: ...

    def schedule(self, video_id: str, publish_at: datetime) -> None: ...
