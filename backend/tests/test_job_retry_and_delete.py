import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.jobs import delete_job, retry_job
from app.core.database import Base
from app.models.tables import AgentTask
from app.services.tasks import mark_task_failed


class JobRetryAndDeleteTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)
        self.db = self.session_factory()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_task(self, status="failed", input_json=None, error="boom", error_json=None):
        task = AgentTask(
            id=f"task-{status}",
            task_type="transcribe_video",
            status=status,
            input_json=input_json if input_json is not None else {"video_id": "video-1"},
            output_json={},
            error=error if status == "failed" else None,
            error_json=error_json if error_json is not None else {"message": error, "error_type": "RuntimeError"},
            trace_id=f"trace-{status}",
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def test_retry_failed_job_requeues_existing_task(self):
        task = self.add_task()

        with patch("app.api.v1.jobs.enqueue_video_task", return_value=True) as enqueue:
            result = retry_job(task.id, self.db, None)

        self.assertEqual(result.status, "pending")
        self.assertIsNone(result.error)
        self.assertEqual(result.error_json, {})
        self.assertIn("retry", result.output_json)
        self.assertEqual(result.output_json["retry"]["previous_error"]["message"], "boom")
        enqueue.assert_called_once_with("transcribe_video", task.id, "video-1", force_new_job=True)

    def test_retry_rejects_non_failed_job(self):
        task = self.add_task(status="running")

        with patch("app.api.v1.jobs.enqueue_video_task") as enqueue:
            with self.assertRaises(HTTPException) as context:
                retry_job(task.id, self.db, None)

        self.assertEqual(context.exception.status_code, 409)
        enqueue.assert_not_called()

    def test_retry_rejects_failed_job_without_video_id(self):
        task = self.add_task(input_json={})

        with patch("app.api.v1.jobs.enqueue_video_task") as enqueue:
            with self.assertRaises(HTTPException) as context:
                retry_job(task.id, self.db, None)

        self.assertEqual(context.exception.status_code, 422)
        enqueue.assert_not_called()

    def test_retry_records_structured_error_when_requeue_fails(self):
        task = self.add_task()

        with patch("app.api.v1.jobs.enqueue_video_task", return_value=False):
            with self.assertRaises(HTTPException) as context:
                retry_job(task.id, self.db, None)

        self.assertEqual(context.exception.status_code, 503)
        refreshed = self.db.get(AgentTask, task.id)
        self.assertEqual(refreshed.status, "failed")
        self.assertEqual(refreshed.error_json["code"], "requeue_failed")
        self.assertEqual(refreshed.error_json["details"]["task_id"], task.id)

    def test_delete_failed_job_removes_task_record(self):
        task = self.add_task()

        response = delete_job(task.id, self.db, None)

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(self.db.get(AgentTask, task.id))

    def test_delete_rejects_non_failed_job(self):
        task = self.add_task(status="succeeded")

        with self.assertRaises(HTTPException) as context:
            delete_job(task.id, self.db, None)

        self.assertEqual(context.exception.status_code, 409)
        self.assertIsNotNone(self.db.get(AgentTask, task.id))

    def test_mark_task_failed_stores_structured_error_json(self):
        task = self.add_task(status="running")

        mark_task_failed(self.db, task.id, ValueError("video missing"), {"stage": "transcribe", "video_id": "video-1"})

        refreshed = self.db.get(AgentTask, task.id)
        self.assertEqual(refreshed.status, "failed")
        self.assertEqual(refreshed.error, "video missing")
        self.assertEqual(refreshed.error_json["message"], "video missing")
        self.assertEqual(refreshed.error_json["error_type"], "ValueError")
        self.assertEqual(refreshed.error_json["stage"], "transcribe")
        self.assertEqual(refreshed.error_json["details"]["video_id"], "video-1")
        self.assertIn("recorded_at", refreshed.error_json)


if __name__ == "__main__":
    unittest.main()
