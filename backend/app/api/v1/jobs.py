from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

from app.api.deps import ApiKey, DbSession
from app.models.tables import AgentTask, VideoClip
from app.schemas.video_ops import JobRead
from app.services.queue import enqueue_clip_export_task, enqueue_video_task
from app.services.tasks import build_task_error

router = APIRouter(prefix="/video-ops/jobs", tags=["jobs"])


def _task_video_id(task: AgentTask) -> str:
    video_id = task.input_json.get("video_id") if isinstance(task.input_json, dict) else None
    if not isinstance(video_id, str) or not video_id.strip():
        raise HTTPException(status_code=422, detail="Job input_json.video_id is required before retry")
    return video_id


def _task_clip_id(task: AgentTask) -> str:
    clip_id = task.input_json.get("clip_id") if isinstance(task.input_json, dict) else None
    if not isinstance(clip_id, str) or not clip_id.strip():
        raise HTTPException(status_code=422, detail="Job input_json.clip_id is required before retry")
    return clip_id


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: DbSession, _: ApiKey) -> AgentTask:
    task = db.get(AgentTask, job_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return task


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(job_id: str, db: DbSession, _: ApiKey) -> AgentTask:
    task = db.get(AgentTask, job_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if task.status != "failed":
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    previous_error = task.error_json or ({"message": task.error} if task.error else {})
    clip: VideoClip | None = None
    clip_id: str | None = None
    video_id: str | None = None
    if task.task_type == "export_clip_video":
        clip_id = _task_clip_id(task)
        clip = db.get(VideoClip, clip_id)
        if clip is None:
            raise HTTPException(status_code=404, detail="Clip not found")
        clip.export_status = "pending"
        clip.export_error = None
    else:
        video_id = _task_video_id(task)
    task.status = "pending"
    task.error = None
    task.error_json = {}
    task.output_json = {
        **(task.output_json or {}),
        "retry": {
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "previous_error": previous_error,
        },
    }
    db.commit()
    if task.task_type == "export_clip_video":
        queued = enqueue_clip_export_task(task.id, clip_id or "", force_new_job=True)
    else:
        queued = enqueue_video_task(task.task_type, task.id, video_id or "", force_new_job=True)
    if not queued:
        task.status = "failed"
        if clip:
            clip.export_status = "failed"
            clip.export_error = "任务重新入队失败"
        task_error = build_task_error(
            "任务重新入队失败",
            {
                "stage": "requeue",
                "task_id": task.id,
                "task_type": task.task_type,
                "video_id": video_id,
                "clip_id": clip_id,
            },
            code="requeue_failed",
        )
        task.error = task_error["message"]
        task.error_json = task_error
        db.commit()
        db.refresh(task)
        raise HTTPException(status_code=503, detail=task_error)
    db.refresh(task)
    return task


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, db: DbSession, _: ApiKey) -> Response:
    task = db.get(AgentTask, job_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if task.status != "failed":
        raise HTTPException(status_code=409, detail="Only failed jobs can be deleted")
    db.delete(task)
    db.commit()
    return Response(status_code=204)
