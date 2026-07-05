from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CandidateClipOutput:
    start_sec: float
    end_sec: float
    reason: str
    highlight: str
    confidence: float
    transcript_text: str = ""


@dataclass(frozen=True)
class CandidateDetectionOutput:
    candidates: list[CandidateClipOutput] = field(default_factory=list)
    prompt_version: str = "candidate-detection-v1"


@dataclass(frozen=True)
class ClipContext:
    clip_id: str
    transcript_text: str
    audience: str = "内容运营"
    score: float = 0.0


@dataclass(frozen=True)
class ClipScoreOutput:
    hook: str
    value_point: str
    audience: str
    semantic_score: float
    reason: str
    prompt_version: str = "clip-score-v1"


@dataclass(frozen=True)
class PublishCopyOutput:
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    cover_text: str = ""
    prompt_version: str = "publish-copy-v1"


@dataclass(frozen=True)
class RiskReviewOutput:
    risk_level: str
    reasons: list[str]
    prompt_version: str = "risk-review-v1"
