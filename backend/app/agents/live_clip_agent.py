from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from typing import Callable, TypeVar

from sqlalchemy.orm import Session

from app.chains.schemas import CandidateClipOutput, ClipContext
from app.core.config import get_settings
from app.models.tables import ChainRun, SourceVideo, TranscriptSegmentModel
from app.services.clip_detection import TranscriptSegment
from app.tools.candidate_detection_tool import CandidateDetectionTool
from app.tools.clip_scoring_tool import ClipScoringTool
from app.tools.publish_copy_tool import PublishCopyTool
from app.tools.risk_review_tool import RiskReviewTool
from app.tools.save_clip_tool import SaveClipTool
from app.tools.transcription_tool import TranscriptionTool


T = TypeVar("T")


class LiveClipAgent:
    """Single-agent orchestrator for the live stream clipping workflow."""

    def __init__(
        self,
        db: Session,
        *,
        candidate_detection_tool: CandidateDetectionTool | None = None,
        transcription_tool: TranscriptionTool | None = None,
        clip_scoring_tool: ClipScoringTool | None = None,
        publish_copy_tool: PublishCopyTool | None = None,
        risk_review_tool: RiskReviewTool | None = None,
        save_clip_tool: SaveClipTool | None = None,
    ) -> None:
        self.db = db
        self.candidate_detection_tool = candidate_detection_tool or CandidateDetectionTool()
        self.transcription_tool = transcription_tool or TranscriptionTool()
        self.clip_scoring_tool = clip_scoring_tool or ClipScoringTool()
        self.publish_copy_tool = publish_copy_tool or PublishCopyTool()
        self.risk_review_tool = risk_review_tool or RiskReviewTool()
        self.save_clip_tool = save_clip_tool or SaveClipTool()

    def save_transcript(self, video_id: str, segments: list[TranscriptSegment]) -> int:
        self.db.query(TranscriptSegmentModel).filter(TranscriptSegmentModel.video_id == video_id).delete()
        for segment in segments:
            self.db.add(
                TranscriptSegmentModel(
                    id=str(uuid.uuid4()),
                    video_id=video_id,
                    start_sec=segment.start_sec,
                    end_sec=segment.end_sec,
                    text=segment.text,
                    confidence=segment.confidence,
                )
            )
        video = self.db.get(SourceVideo, video_id)
        if video:
            video.status = "transcribed"
        self.db.commit()
        return len(segments)

    def transcribe_video(self, video_id: str) -> int:
        video = self.db.get(SourceVideo, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")
        segments = self.transcription_tool.run(video.file_uri, duration_sec=video.duration_sec)
        return self.save_transcript(video_id=video_id, segments=segments)

    def detect_clips(self, video_id: str, trace_id: str) -> int:
        segments = self._load_transcript_segments(video_id)
        if not segments:
            raise ValueError("Video transcript is required before detecting candidate clips")

        detected = self._record_chain_run(
            clip_id=None,
            chain_name="candidate_detection",
            trace_id=trace_id,
            prompt_version="candidate-detection-v1",
            model=self._model_name(),
            input_json={"segments": [asdict(segment) for segment in segments]},
            call=lambda: self.candidate_detection_tool.run(segments),
        )

        created = 0
        for candidate in self._valid_candidates(detected.candidates, segments):
            clip_id = str(uuid.uuid4())
            transcript_text = candidate.transcript_text or self._transcript_text_for_range(
                segments,
                candidate.start_sec,
                candidate.end_sec,
            )
            context = ClipContext(
                clip_id=clip_id,
                transcript_text=transcript_text,
                audience="内容运营",
                score=candidate.confidence,
            )
            scored = self._record_chain_run(
                clip_id=clip_id,
                chain_name="clip_scoring",
                trace_id=trace_id,
                prompt_version="clip-score-v1",
                model=self._model_name(),
                input_json={
                    "transcript_text": context.transcript_text,
                    "score": context.score,
                    "selection_reason": candidate.reason,
                    "highlight": candidate.highlight,
                },
                call=lambda context=context: self.clip_scoring_tool.run(context),
            )
            copy = self._record_chain_run(
                clip_id=clip_id,
                chain_name="publish_copy",
                trace_id=trace_id,
                prompt_version="publish-copy-v1",
                model=self._model_name(),
                input_json={"transcript_text": context.transcript_text, "audience": context.audience},
                call=lambda context=context: self.publish_copy_tool.run(context),
            )
            risk = self._record_chain_run(
                clip_id=clip_id,
                chain_name="risk_review",
                trace_id=trace_id,
                prompt_version="risk-review-v1",
                model=self._risk_model_name(),
                input_json=asdict(copy),
                call=lambda copy=copy: self.risk_review_tool.run(copy),
            )
            self.save_clip_tool.run(
                self.db,
                clip_id=clip_id,
                video_id=video_id,
                start_sec=candidate.start_sec,
                end_sec=candidate.end_sec,
                score=scored,
                copy=copy,
                risk=risk,
            )
            created += 1

        video = self.db.get(SourceVideo, video_id)
        if video:
            video.status = "clips_detected"
        self.db.commit()
        return created

    def _load_transcript_segments(self, video_id: str) -> list[TranscriptSegment]:
        rows = (
            self.db.query(TranscriptSegmentModel)
            .filter(TranscriptSegmentModel.video_id == video_id)
            .order_by(TranscriptSegmentModel.start_sec)
            .all()
        )
        return [
            TranscriptSegment(
                start_sec=row.start_sec,
                end_sec=row.end_sec,
                text=row.text,
                confidence=row.confidence,
            )
            for row in rows
        ]

    def _valid_candidates(
        self,
        candidates: list[CandidateClipOutput],
        segments: list[TranscriptSegment],
    ) -> list[CandidateClipOutput]:
        if not segments:
            return []

        start_bound = min(segment.start_sec for segment in segments)
        end_bound = max(segment.end_sec for segment in segments)
        selected: list[CandidateClipOutput] = []
        ranked_candidates = [(candidate.confidence, index, candidate) for index, candidate in enumerate(candidates)]
        ranked_candidates.sort(reverse=True)
        ordered_candidates = [candidate for _, _, candidate in ranked_candidates]
        for candidate in ordered_candidates:
            if candidate.start_sec < start_bound or candidate.end_sec > end_bound:
                continue
            if candidate.end_sec <= candidate.start_sec:
                continue
            if candidate.end_sec - candidate.start_sec > 120:
                continue
            text = candidate.transcript_text or self._transcript_text_for_range(
                segments,
                candidate.start_sec,
                candidate.end_sec,
            )
            if not text.strip():
                continue
            if any(self._overlap_ratio(candidate, existing) > 0.6 for existing in selected):
                continue
            selected.append(
                CandidateClipOutput(
                    start_sec=candidate.start_sec,
                    end_sec=candidate.end_sec,
                    reason=candidate.reason,
                    highlight=candidate.highlight,
                    confidence=min(max(candidate.confidence, 0.0), 1.0),
                    transcript_text=text,
                )
            )
        return selected

    def _transcript_text_for_range(
        self,
        segments: list[TranscriptSegment],
        start_sec: float,
        end_sec: float,
    ) -> str:
        return " ".join(
            segment.text.strip()
            for segment in segments
            if segment.end_sec > start_sec and segment.start_sec < end_sec and segment.text.strip()
        )

    def _overlap_ratio(self, left: CandidateClipOutput, right: CandidateClipOutput) -> float:
        overlap = max(0.0, min(left.end_sec, right.end_sec) - max(left.start_sec, right.start_sec))
        shortest = min(left.end_sec - left.start_sec, right.end_sec - right.start_sec)
        if shortest <= 0:
            return 0.0
        return overlap / shortest

    def _record_chain_run(
        self,
        *,
        clip_id: str | None,
        chain_name: str,
        trace_id: str,
        prompt_version: str,
        model: str,
        input_json: dict,
        call: Callable[[], T],
    ) -> T:
        started = time.perf_counter()
        error = None
        output_json = {}
        try:
            output = call()
            output_json = asdict(output)
            return output
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self.db.add(
                ChainRun(
                    id=str(uuid.uuid4()),
                    clip_id=clip_id,
                    chain_name=chain_name,
                    prompt_version=prompt_version,
                    model=model,
                    input_json=input_json,
                    output_json=output_json,
                    latency_ms=latency_ms,
                    error=error,
                    trace_id=trace_id,
                )
            )

    def _model_name(self) -> str:
        settings = get_settings()
        return "mock" if settings.llm_mock else settings.llm_model

    def _risk_model_name(self) -> str:
        settings = get_settings()
        return "rules" if settings.llm_mock else settings.llm_model
