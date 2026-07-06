from __future__ import annotations

from uuid import uuid4

from app.core.config import get_settings
from app.jobs.queues import VIDEO_OPS_QUEUE


def enqueue_video_task(task_type: str, task_id: str, video_id: str, *, force_new_job: bool = False) -> bool:
    """Enqueue an RQ job when Redis is available; leave task pending otherwise."""

    try:
        from redis import Redis
        from rq import Queue

        from app.jobs.pipeline import detect_clips_job, transcribe_video_job

        settings = get_settings()
        redis_conn = Redis.from_url(settings.redis_url)
        queue = Queue(VIDEO_OPS_QUEUE, connection=redis_conn)
        rq_job_id = f"{task_id}:retry:{uuid4()}" if force_new_job else task_id
        if task_type == "transcribe_video":
            queue.enqueue(transcribe_video_job, task_id, video_id, job_id=rq_job_id)
            return True
        if task_type == "detect_clips":
            queue.enqueue(detect_clips_job, task_id, video_id, job_id=rq_job_id)
            return True
    except Exception:
        return False
    return False


def enqueue_clip_export_task(task_id: str, clip_id: str, *, force_new_job: bool = False) -> bool:
    """Enqueue an RQ job that exports an approved clip into a video file."""

    try:
        from redis import Redis
        from rq import Queue

        from app.jobs.pipeline import export_clip_video_job

        settings = get_settings()
        redis_conn = Redis.from_url(settings.redis_url)
        queue = Queue(VIDEO_OPS_QUEUE, connection=redis_conn)
        rq_job_id = f"{task_id}:retry:{uuid4()}" if force_new_job else task_id
        queue.enqueue(export_clip_video_job, task_id, clip_id, job_id=rq_job_id)
        return True
    except Exception:
        return False
