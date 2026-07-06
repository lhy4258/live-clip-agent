from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.tables import AgentTask, VideoClip
from app.services.agent_pipeline import VideoOpsAgentPipeline
from app.services.tasks import mark_task_failed, mark_task_running, mark_task_succeeded
from app.tools.export_clip_video_tool import ExportClipVideoTool


def transcribe_video_job(task_id: str, video_id: str) -> None:
    db = SessionLocal()
    try:
        mark_task_running(db, task_id)
        count = VideoOpsAgentPipeline(db).transcribe_video(video_id)
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


def export_clip_video_job(task_id: str, clip_id: str) -> None:
    db = SessionLocal()
    try:
        mark_task_running(db, task_id)
        clip = db.get(VideoClip, clip_id)
        if clip is None:
            raise ValueError("Clip not found")
        if clip.video is None:
            raise ValueError("Source video not found")

        clip.export_status = "exporting"
        clip.export_error = None
        db.commit()

        settings = get_settings()
        tool = ExportClipVideoTool(Path(settings.storage_dir) / "clips")
        clip_file_uri = tool.run(
            source_file_uri=clip.video.file_uri,
            start_sec=clip.start_sec,
            end_sec=clip.end_sec,
            clip_id=clip.id,
        )

        clip.export_status = "exported"
        clip.clip_file_uri = clip_file_uri
        clip.export_error = None
        clip.exported_at = datetime.now(timezone.utc)
        db.commit()
        mark_task_succeeded(db, task_id, {"clip_id": clip_id, "clip_file_uri": clip_file_uri})
    except Exception as exc:
        db.rollback()
        clip = db.get(VideoClip, clip_id)
        if clip:
            clip.export_status = "failed"
            clip.export_error = str(exc)
            db.commit()
        mark_task_failed(db, task_id, exc, {"stage": "export_clip_video", "clip_id": clip_id})
        raise
    finally:
        db.close()
