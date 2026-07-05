from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import ApiKey, DbSession
from app.models.tables import ClipReview, PublishPlan, VideoClip
from app.schemas.video_ops import ClipRead, ClipReviewCreate, PublishPlanCreate, PublishPlanRead

router = APIRouter(prefix="/video-ops/clips", tags=["clips"])


@router.get("", response_model=list[ClipRead])
def list_clips(db: DbSession, _: ApiKey, status_filter: str | None = None) -> list[VideoClip]:
    query = select(VideoClip).order_by(VideoClip.score.desc())
    if status_filter:
        query = query.where(VideoClip.status == status_filter)
    return list(db.scalars(query).all())


@router.get("/{clip_id}", response_model=ClipRead)
def get_clip(clip_id: str, db: DbSession, _: ApiKey) -> VideoClip:
    clip = db.get(VideoClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.post("/{clip_id}/review", response_model=ClipRead)
def review_clip(clip_id: str, payload: ClipReviewCreate, db: DbSession, _: ApiKey) -> VideoClip:
    clip = db.get(VideoClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    db.add(ClipReview(clip_id=clip_id, label=payload.label, reason=payload.reason, reviewer=payload.reviewer))
    clip.status = payload.label
    db.commit()
    db.refresh(clip)
    return clip


@router.post("/{clip_id}/publish-plan", response_model=PublishPlanRead, status_code=status.HTTP_201_CREATED)
def create_publish_plan(clip_id: str, payload: PublishPlanCreate, db: DbSession, _: ApiKey) -> PublishPlan:
    clip = db.get(VideoClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    plan = PublishPlan(
        clip_id=clip_id,
        platform=payload.platform,
        title=clip.title,
        description=clip.summary,
        hashtags=clip.tags,
        status="draft",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
