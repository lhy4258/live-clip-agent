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
        is_editable, edit_suggestion, edit_reason = self._edit_reference(score, risk)
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
            is_editable=is_editable,
            edit_suggestion=edit_suggestion,
            edit_reason=edit_reason,
            risk_level=risk.risk_level,
        )
        db.add(clip)
        return clip

    def _edit_reference(self, score: ClipScoreOutput, risk: RiskReviewOutput) -> tuple[bool, str, str]:
        suggestions: list[str] = []
        reasons: list[str] = []

        if score.semantic_score < 0.82:
            suggestions.append("建议补强标题、封面文案或摘要中的用户收益点。")
            reasons.append(f"语义评分为 {score.semantic_score:.2f}，内容价值需要人工再判断。")

        if risk.risk_level in {"medium", "high"}:
            suggestions.append("建议检查标题、封面文案和标签，避免夸大承诺或敏感表达。")
            risk_reasons = "；".join(reason for reason in risk.reasons if reason)
            reasons.append(risk_reasons or f"风控等级为 {risk.risk_level}，需要人工复核表达风险。")

        if not suggestions:
            return False, "", ""

        return True, "；".join(suggestions), "；".join(reasons)
