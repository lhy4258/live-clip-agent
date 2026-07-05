from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VideoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    file_uri: str = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, max_length=120)
    license: str = Field(min_length=1, max_length=120)
    duration_sec: float | None = None


class VideoRead(BaseModel):
    id: str
    title: str
    file_uri: str
    duration_sec: float | None
    source: str
    license: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JobRead(BaseModel):
    id: str
    task_type: str
    status: str
    error: str | None
    trace_id: str
    input_json: dict
    output_json: dict
    error_json: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class TranscriptSegmentRead(BaseModel):
    id: str
    video_id: str
    start_sec: float
    end_sec: float
    text: str
    confidence: float

    model_config = {"from_attributes": True}


class ClipRead(BaseModel):
    id: str
    video_id: str
    start_sec: float
    end_sec: float
    title: str
    summary: str
    tags: list[str]
    cover_text: str
    score: float
    status: str
    risk_level: str

    model_config = {"from_attributes": True}


class ClipReviewCreate(BaseModel):
    label: str = Field(pattern="^(approved|rejected|needs_edit)$")
    reason: str = ""
    reviewer: str = Field(min_length=1, max_length=120)


class PublishPlanCreate(BaseModel):
    platform: str = Field(default="douyin", max_length=80)


class PublishPlanRead(BaseModel):
    id: str
    clip_id: str
    platform: str
    title: str
    description: str
    hashtags: list[str]
    status: str

    model_config = {"from_attributes": True}


class ChainRunRead(BaseModel):
    id: str
    clip_id: str | None
    chain_name: str
    prompt_version: str
    model: str
    input_json: dict
    output_json: dict
    latency_ms: int
    error: str | None
    trace_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
