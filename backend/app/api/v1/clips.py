from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.api.deps import ApiKey, DbSession
from app.models.tables import ClipReview, PublishPlan, VideoClip
from app.schemas.video_ops import ClipCoverTextUpdate, ClipRead, ClipReviewCreate, JobRead, PublishPlanCreate, PublishPlanRead
from app.services.queue import enqueue_clip_export_task
from app.services.tasks import create_task

router = APIRouter(prefix="/video-ops/clips", tags=["clips"])


@router.get("", response_model=list[ClipRead])
def list_clips(db: DbSession, _: ApiKey, status_filter: str | None = None) -> list[VideoClip]:
    query = select(VideoClip).options(selectinload(VideoClip.video)).order_by(VideoClip.score.desc())
    if status_filter:
        query = query.where(VideoClip.status == status_filter)
    return list(db.scalars(query).all())


@router.get("/{clip_id}", response_model=ClipRead)
def get_clip(clip_id: str, db: DbSession, _: ApiKey) -> VideoClip:
    clip = db.scalars(select(VideoClip).options(selectinload(VideoClip.video)).where(VideoClip.id == clip_id)).one_or_none()
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clip(clip_id: str, db: DbSession, _: ApiKey) -> Response:
    clip = db.get(VideoClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    if clip.status == "approved":
        raise HTTPException(status_code=409, detail="Approved clips cannot be deleted")

    db.execute(delete(ClipReview).where(ClipReview.clip_id == clip_id))
    db.execute(delete(PublishPlan).where(PublishPlan.clip_id == clip_id))
    db.delete(clip)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.patch("/{clip_id}/cover-text", response_model=ClipRead)
def update_clip_cover_text(clip_id: str, payload: ClipCoverTextUpdate, db: DbSession, _: ApiKey) -> VideoClip:
    clip = db.get(VideoClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.cover_text = payload.cover_text
    db.commit()
    db.refresh(clip)
    return clip


@router.post("/{clip_id}/export", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def export_clip(clip_id: str, db: DbSession, _: ApiKey):
    clip = db.get(VideoClip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    if clip.status != "approved":
        raise HTTPException(status_code=409, detail="Only approved clips can be exported")
    if clip.export_status in {"pending", "exporting"}:
        raise HTTPException(status_code=409, detail="Clip export is already queued or running")
    if clip.export_status == "exported":
        raise HTTPException(status_code=409, detail="Clip has already been exported")

    task = create_task(db, "export_clip_video", {"clip_id": clip_id, "video_id": clip.video_id})
    clip.export_status = "pending"
    clip.export_error = None
    db.commit()
    enqueue_clip_export_task(task.id, clip_id)
    db.refresh(task)
    return task


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
