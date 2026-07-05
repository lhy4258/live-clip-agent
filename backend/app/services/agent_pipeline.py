from __future__ import annotations

import time
import uuid
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.chains.clip_scoring import ClipScoringChain
from app.chains.publish_copy import PublishCopyChain
from app.chains.risk_review import RiskReviewChain
from app.chains.schemas import ClipContext
from app.core.config import get_settings
from app.models.tables import ChainRun, SourceVideo, TranscriptSegmentModel, VideoClip
from app.services.clip_detection import ClipRuleEngine, TranscriptSegment


DEFAULT_KEYWORDS = ["收益点", "痛点", "案例", "方法", "步骤", "建议"]


class VideoOpsAgentPipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.clip_engine = ClipRuleEngine(keywords=DEFAULT_KEYWORDS)
        self.scoring_chain = ClipScoringChain(mock=settings.llm_mock)
        self.publish_chain = PublishCopyChain(mock=settings.llm_mock)
        self.risk_chain = RiskReviewChain(mock=settings.llm_mock)

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

    def detect_clips(self, video_id: str, trace_id: str) -> int:
        rows = (
            self.db.query(TranscriptSegmentModel)
            .filter(TranscriptSegmentModel.video_id == video_id)
            .order_by(TranscriptSegmentModel.start_sec)
            .all()
        )
        segments = [
            TranscriptSegment(
                start_sec=row.start_sec,
                end_sec=row.end_sec,
                text=row.text,
                confidence=row.confidence,
            )
            for row in rows
        ]
        candidates = self.clip_engine.generate_candidates(video_id=video_id, segments=segments)
        created = 0
        for candidate in candidates:
            context = ClipContext(
                clip_id=str(uuid.uuid4()),
                transcript_text=candidate.transcript_text,
                audience="内容运营",
                score=candidate.score,
            )
            scored = self._record_chain_run(
                clip_id=None,
                chain_name="clip_scoring",
                trace_id=trace_id,
                prompt_version="clip-score-v1",
                model="mock" if get_settings().llm_mock else get_settings().llm_model,
                input_json={"transcript_text": context.transcript_text, "score": context.score},
                call=lambda: self.scoring_chain.score(context),
            )
            copy = self._record_chain_run(
                clip_id=None,
                chain_name="publish_copy",
                trace_id=trace_id,
                prompt_version="publish-copy-v1",
                model="mock" if get_settings().llm_mock else get_settings().llm_model,
                input_json={"transcript_text": context.transcript_text, "audience": context.audience},
                call=lambda: self.publish_chain.generate(context),
            )
            risk = self._record_chain_run(
                clip_id=None,
                chain_name="risk_review",
                trace_id=trace_id,
                prompt_version="risk-review-v1",
                model="rules" if get_settings().llm_mock else get_settings().llm_model,
                input_json=asdict(copy),
                call=lambda: self.risk_chain.review(copy),
            )
            self.db.add(
                VideoClip(
                    id=context.clip_id,
                    video_id=video_id,
                    start_sec=candidate.start_sec,
                    end_sec=candidate.end_sec,
                    title=copy.title,
                    summary=scored.value_point,
                    tags=copy.tags,
                    cover_text=copy.cover_text,
                    score=scored.semantic_score,
                    status="candidate",
                    risk_level=risk.risk_level,
                )
            )
            created += 1
        video = self.db.get(SourceVideo, video_id)
        if video:
            video.status = "clips_detected"
        self.db.commit()
        return created

    def _record_chain_run(
        self,
        clip_id: str | None,
        chain_name: str,
        trace_id: str,
        prompt_version: str,
        model: str,
        input_json: dict,
        call,
    ):
        started = time.perf_counter()
        error = None
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
                    output_json=output_json if error is None else {},
                    latency_ms=latency_ms,
                    error=error,
                    trace_id=trace_id,
                )
            )
