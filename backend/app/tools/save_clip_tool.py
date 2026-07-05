from __future__ import annotations

from sqlalchemy.orm import Session

from app.chains.publish_copy import PublishCopyOutput
from app.chains.schemas import ClipScoreOutput, RiskReviewOutput
from app.models.tables import VideoClip


class SaveClipTool:
    def run(
        self,
        db: Session,
        *,
        clip_id: str,
        video_id: str,
        start_sec: float,
        end_sec: float,
        score: ClipScoreOutput,
        copy: PublishCopyOutput,
        risk: RiskReviewOutput,
    ) -> VideoClip:
        clip = VideoClip(
            id=clip_id,
            video_id=video_id,
            start_sec=start_sec,
            end_sec=end_sec,
            title=copy.title,
            summary=score.value_point,
            tags=copy.tags,
            cover_text=copy.cover_text,
            score=score.semantic_score,
            status="candidate",
            risk_level=risk.risk_level,
        )
        db.add(clip)
        return clip
