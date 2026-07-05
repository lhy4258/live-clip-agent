from __future__ import annotations

from app.core.database import SessionLocal
from app.models.tables import AgentTask, SourceVideo
from app.services.agent_pipeline import VideoOpsAgentPipeline
from app.services.tasks import mark_task_failed, mark_task_running, mark_task_succeeded
from app.services.transcription import TranscriptionService


def transcribe_video_job(task_id: str, video_id: str) -> None:
    db = SessionLocal()
    try:
        mark_task_running(db, task_id)
        video = db.get(SourceVideo, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")
        segments = TranscriptionService(mock=True).transcribe(video.file_uri)
        count = VideoOpsAgentPipeline(db).save_transcript(video_id=video_id, segments=segments)
        mark_task_succeeded(db, task_id, {"segments": count})
    except Exception as exc:
        mark_task_failed(db, task_id, exc, {"stage": "transcribe", "video_id": video_id})
        raise
    finally:
        db.close()


def detect_clips_job(task_id: str, video_id: str) -> None:
    db = SessionLocal()
    try:
        mark_task_running(db, task_id)
        task = db.get(AgentTask, task_id)
        trace_id = task.trace_id if task else task_id
        count = VideoOpsAgentPipeline(db).detect_clips(video_id=video_id, trace_id=trace_id)
        mark_task_succeeded(db, task_id, {"clips": count})
    except Exception as exc:
        mark_task_failed(db, task_id, exc, {"stage": "detect_clips", "video_id": video_id})
        raise
    finally:
        db.close()
