from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import ApiKey, DbSession
from app.core.config import get_settings
from app.models.tables import SourceVideo
from app.schemas.video_ops import JobRead, TranscriptSegmentRead, VideoCreate, VideoRead
from app.services.queue import enqueue_video_task
from app.services.storage import VideoStorageService
from app.services.tasks import create_task

router = APIRouter(prefix="/video-ops/videos", tags=["videos"])


@router.post("", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
def create_video(payload: VideoCreate, db: DbSession, _: ApiKey) -> SourceVideo:
    video = SourceVideo(**payload.model_dump())
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.post("/upload", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
async def upload_video(
    db: DbSession,
    _: ApiKey,
    title: str = Form(min_length=1, max_length=200),
    source: str = Form(default="self_recorded", min_length=1, max_length=120),
    license: str = Form(default="self_owned", min_length=1, max_length=120),
    duration_sec: float | None = Form(default=None),
    file: UploadFile = File(...),
) -> SourceVideo:
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(status_code=415, detail="Only video uploads are supported")

    settings = get_settings()
    file_uri = await VideoStorageService(settings.storage_dir).save_upload(file)
    video = SourceVideo(
        title=title,
        file_uri=file_uri,
        duration_sec=duration_sec,
        source=source,
        license=license,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("", response_model=list[VideoRead])
def list_videos(db: DbSession, _: ApiKey) -> list[SourceVideo]:
    return list(db.scalars(select(SourceVideo).order_by(SourceVideo.created_at.desc())).all())


@router.get("/{video_id}", response_model=VideoRead)
def get_video(video_id: str, db: DbSession, _: ApiKey) -> SourceVideo:
    video = db.get(SourceVideo, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/transcripts", response_model=list[TranscriptSegmentRead])
def list_transcripts(video_id: str, db: DbSession, _: ApiKey):
    video = db.get(SourceVideo, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video.transcripts


@router.post("/{video_id}/transcribe", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def transcribe_video(video_id: str, db: DbSession, _: ApiKey):
    if db.get(SourceVideo, video_id) is None:
        raise HTTPException(status_code=404, detail="Video not found")
    task = create_task(db, "transcribe_video", {"video_id": video_id})
    enqueue_video_task("transcribe_video", task.id, video_id)
    return task


@router.post("/{video_id}/detect-clips", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def detect_video_clips(video_id: str, db: DbSession, _: ApiKey):
    if db.get(SourceVideo, video_id) is None:
        raise HTTPException(status_code=404, detail="Video not found")
    task = create_task(db, "detect_clips", {"video_id": video_id})
    enqueue_video_task("detect_clips", task.id, video_id)
    return task
