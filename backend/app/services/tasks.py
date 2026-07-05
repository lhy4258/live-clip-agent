from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.tables import AgentTask


def build_task_error(error: Exception | str, details: dict[str, Any] | None = None, code: str = "task_failed") -> dict:
    details = dict(details or {})
    stage = details.pop("stage", None)
    message = str(error)
    error_type = error.__class__.__name__ if isinstance(error, Exception) else "TaskError"
    return {
        "code": code,
        "message": message,
        "error_type": error_type,
        "stage": stage,
        "details": details,
        "retryable": True,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def create_task(db: Session, task_type: str, input_json: dict, trace_id: str | None = None) -> AgentTask:
    task = AgentTask(
        id=str(uuid.uuid4()),
        task_type=task_type,
        status="pending",
        input_json=input_json,
        output_json={},
        error_json={},
        trace_id=trace_id or str(uuid.uuid4()),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def mark_task_running(db: Session, task_id: str) -> None:
    task = db.get(AgentTask, task_id)
    if task:
        task.status = "running"
        db.commit()


def mark_task_succeeded(db: Session, task_id: str, output_json: dict) -> None:
    task = db.get(AgentTask, task_id)
    if task:
        task.status = "succeeded"
        task.output_json = output_json
        task.error = None
        task.error_json = {}
        db.commit()


def mark_task_failed(
    db: Session,
    task_id: str,
    error: Exception | str,
    details: dict[str, Any] | None = None,
    code: str = "task_failed",
) -> None:
    task = db.get(AgentTask, task_id)
    if task:
        task.status = "failed"
        task_error = build_task_error(error, details, code)
        task.error = task_error["message"]
        task.error_json = task_error
        db.commit()
