from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


FILLER_TOKENS = ("嗯", "呃", "然后", "这个", "那个")


@dataclass(frozen=True)
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str
    confidence: float = 1.0


@dataclass(frozen=True)
class ClipCandidate:
    video_id: str
    start_sec: float
    end_sec: float
    transcript_text: str
    score: float
    matched_keywords: list[str]


class ClipRuleEngine:
    """Deterministic candidate generator before model scoring."""

    def __init__(
        self,
        keywords: Iterable[str] | None = None,
        min_duration_sec: int = 20,
        max_duration_sec: int = 90,
    ) -> None:
        self.keywords = [keyword for keyword in (keywords or []) if keyword]
        self.min_duration_sec = min_duration_sec
        self.max_duration_sec = max_duration_sec

    def generate_candidates(self, video_id: str, segments: list[TranscriptSegment]) -> list[ClipCandidate]:
        ordered = sorted(segments, key=lambda segment: segment.start_sec)
        candidates: list[ClipCandidate] = []

        for start_index in range(len(ordered)):
            window: list[TranscriptSegment] = []
            for segment in ordered[start_index:]:
                window.append(segment)
                duration = window[-1].end_sec - window[0].start_sec
                if duration < self.min_duration_sec:
                    continue
                if duration > self.max_duration_sec:
                    break

                text = " ".join(item.text.strip() for item in window if item.text.strip())
                if self._is_low_value_text(text):
                    continue

                matched = [keyword for keyword in self.keywords if keyword in text]
                score = self._score_window(text=text, matched_keywords=matched, segments=window)
                if score >= 0.5:
                    candidates.append(
                        ClipCandidate(
                            video_id=video_id,
                            start_sec=window[0].start_sec,
                            end_sec=window[-1].end_sec,
                            transcript_text=text,
                            score=round(score, 3),
                            matched_keywords=matched,
                        )
                    )

        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return self._dedupe_overlapping(candidates)

    def _score_window(
        self,
        text: str,
        matched_keywords: list[str],
        segments: list[TranscriptSegment],
    ) -> float:
        keyword_score = min(len(matched_keywords) * 0.2, 0.45)
        confidence_score = sum(segment.confidence for segment in segments) / max(len(segments), 1) * 0.2
        structure_score = 0.25 if any(word in text for word in ("第一", "第二", "步骤", "案例", "建议")) else 0.1
        density_score = min(len(text) / 180, 0.2)
        return keyword_score + confidence_score + structure_score + density_score

    def _is_low_value_text(self, text: str) -> bool:
        if not text.strip():
            return True
        stripped = text.replace(" ", "")
        filler_chars = sum(stripped.count(token) * len(token) for token in FILLER_TOKENS)
        if len(stripped) == 0:
            return True
        return filler_chars / len(stripped) >= 0.5

    def _dedupe_overlapping(self, candidates: list[ClipCandidate]) -> list[ClipCandidate]:
        selected: list[ClipCandidate] = []
        for candidate in candidates:
            if not any(self._overlap_ratio(candidate, existing) > 0.6 for existing in selected):
                selected.append(candidate)
        return selected

    def _overlap_ratio(self, left: ClipCandidate, right: ClipCandidate) -> float:
        overlap = max(0.0, min(left.end_sec, right.end_sec) - max(left.start_sec, right.start_sec))
        shortest = min(left.end_sec - left.start_sec, right.end_sec - right.start_sec)
        if shortest <= 0:
            return 0.0
        return overlap / shortest
